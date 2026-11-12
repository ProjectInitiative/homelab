#!/usr/bin/env python3
"""End-to-end watchdog for Tailscale Kubernetes VIP Services."""
import base64
import hashlib
import json
import os
import socket
import ssl
import time
import traceback
import urllib.parse
import urllib.request

PROXY_NS = os.environ.get("PROXY_NS", "tailscale")
OPERATOR_NAME = os.environ.get("OPERATOR_NAME", "operator")
FAILURES_BEFORE_REPAIR = int(os.environ.get("FAILURES_BEFORE_REPAIR", "3"))
RESTART_GRACE = int(os.environ.get("RESTART_GRACE", "180"))
REPAIR_RETRY = int(os.environ.get("REPAIR_RETRY", "60"))
POST_REPAIR_GRACE = int(os.environ.get("POST_REPAIR_GRACE", "60"))
VIP_RECREATE_WAIT = int(os.environ.get("VIP_RECREATE_WAIT", "120"))
VIP_RECREATE_SETTLE = int(os.environ.get("VIP_RECREATE_SETTLE", "15"))
INTERVAL = int(os.environ.get("INTERVAL", "30"))
TOKEN = open("/var/run/secrets/kubernetes.io/serviceaccount/token").read().strip()
CA = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
KUBE = os.environ.get("KUBERNETES_SERVICE_HOST", "kubernetes.default.svc")
KUBE_PORT = os.environ.get("KUBERNETES_SERVICE_PORT", "443")
KUBE_BASE = f"https://{KUBE}:{KUBE_PORT}"
SSL = ssl.create_default_context(cafile=CA)


def request(url, method="GET", body=None, headers=None, context=None):
    hdrs = {"Authorization": f"Bearer {TOKEN}"} if url.startswith(KUBE_BASE) else {}
    hdrs.update(headers or {})
    if body is not None and "Content-Type" not in hdrs:
        hdrs["Content-Type"] = "application/strategic-merge-patch+json" if method == "PATCH" else "application/json"
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=15, context=context or (SSL if url.startswith(KUBE_BASE) else None)) as resp:
        raw = resp.read()
        return resp.status, json.loads(raw) if raw else None


def kube(path, method="GET", body=None):
    return request(KUBE_BASE + path, method, body)


def ha_proxy_groups():
    # ProxyGroup is cluster-scoped; only the owning StatefulSet is namespaced.
    _, data = kube("/apis/tailscale.com/v1alpha1/proxygroups")
    return {
        item["metadata"]["name"]
        for item in (data.get("items") or [])
        if item.get("spec", {}).get("type") == "ingress"
        and int(item.get("spec", {}).get("replicas", 1)) > 1
    }


def services(proxy_groups):
    _, data = kube("/api/v1/services")
    result = []
    for service in (data.get("items") or []):
        annotations = service.get("metadata", {}).get("annotations", {})
        proxy_group = annotations.get("tailscale.com/proxy-group")
        if proxy_group in proxy_groups and service.get("spec", {}).get("loadBalancerClass") == "tailscale":
            result.append(service)
    return result


def endpoints_by_service():
    _, data = kube("/apis/discovery.k8s.io/v1/endpointslices")
    counts = {}
    fingerprints = {}
    for sl in (data.get("items") or []):
        metadata = sl.get("metadata") or {}
        labels = metadata.get("labels") or {}
        name = labels.get("kubernetes.io/service-name")
        namespace = metadata.get("namespace")
        if not name:
            continue
        key = (namespace, name)
        endpoints = sl.get("endpoints") or []
        counts[key] = counts.get(key, 0) + sum(1 for ep in endpoints if ep.get("conditions", {}).get("ready") is True)
        fingerprints.setdefault(key, []).append({
            "name": metadata.get("name"),
            "endpoints": sorted(endpoints, key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"))),
            "ports": sorted(sl.get("ports") or [], key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":"))),
        })
    for key, slices in fingerprints.items():
        encoded = json.dumps(sorted(slices, key=lambda item: item.get("name") or ""), sort_keys=True, separators=(",", ":")).encode()
        fingerprints[key] = hashlib.sha256(encoded).hexdigest()
    return counts, fingerprints


def vip_ips(service):
    status = service.get("status") or {}
    load_balancer = status.get("loadBalancer") or {}
    ingress = load_balancer.get("ingress") or []
    return [x.get("ip") for x in ingress if x.get("ip")]


def probe(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=5):
            return True
    except OSError as exc:
        print(f"probe {ip}:{port} failed: {type(exc).__name__}: {exc}", flush=True)
        return False


def service_healthy(service, endpoint_counts):
    key = (service["metadata"].get("namespace"), service["metadata"].get("name"))
    if endpoint_counts.get(key, 0) == 0:
        return False, 0
    ports = [int(p["port"]) for p in service.get("spec", {}).get("ports", []) if p.get("port")]
    ips = vip_ips(service)
    return any(probe(ip, port) for ip in ips for port in ports), endpoint_counts[key]


def proxy_pods(sts):
    selector = sts.get("spec", {}).get("selector", {}).get("matchLabels") or {}
    selector_text = ",".join(f"{key}={value}" for key, value in sorted(selector.items()))
    pod_path = f"/api/v1/namespaces/{PROXY_NS}/pods?labelSelector={urllib.parse.quote(selector_text, safe='=,')}"
    _, pod_data = kube(pod_path)
    return [pod for pod in (pod_data.get("items") or []) if not pod.get("metadata", {}).get("deletionTimestamp")]


def proxy_group_ready(proxy_group):
    path = f"/apis/tailscale.com/v1alpha1/proxygroups/{urllib.parse.quote(proxy_group, safe='')}"
    _, data = kube(path)
    conditions = data.get("status", {}).get("conditions") or []
    return all(
        any(condition.get("type") == condition_type and condition.get("status") == "True" for condition in conditions)
        for condition_type in ("ProxyGroupAvailable", "ProxyGroupReady")
    )


def pod_ready(pod):
    return any(
        condition.get("type") == "Ready" and condition.get("status") == "True"
        for condition in pod.get("status", {}).get("conditions", [])
    )


def pod_ordinal(pod):
    try:
        return int(pod.get("metadata", {}).get("name", "").rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return -1


def proxy_rollout_status(proxy_group):
    path = f"/apis/apps/v1/namespaces/{PROXY_NS}/statefulsets/{urllib.parse.quote(proxy_group, safe='')}"
    _, sts = kube(path)
    spec = sts.get("spec") or {}
    status = sts.get("status") or {}
    replicas = int(spec.get("replicas", 0))
    pods = proxy_pods(sts)
    target_revision = status.get("updateRevision")
    pods_on_revision = sum(1 for pod in pods if pod.get("metadata", {}).get("labels", {}).get("controller-revision-hash") == target_revision)
    pods_ready_on_revision = sum(
        1
        for pod in pods
        if pod.get("metadata", {}).get("labels", {}).get("controller-revision-hash") == target_revision and pod_ready(pod)
    )
    rollout = rollouts.get(proxy_group)
    details = {
        "generation": sts.get("metadata", {}).get("generation", 0),
        "observedGeneration": status.get("observedGeneration", 0),
        "replicas": replicas,
        "updatedReplicas": status.get("updatedReplicas", 0),
        "readyReplicas": status.get("readyReplicas", 0),
        "availableReplicas": status.get("availableReplicas", 0),
        "podsOnRevision": pods_on_revision,
        "podsReadyOnRevision": pods_ready_on_revision,
        "currentRevision": status.get("currentRevision"),
        "targetRevision": target_revision,
        "updateRevision": status.get("updateRevision"),
        "proxyGroupReady": proxy_group_ready(proxy_group),
        "rolloutPending": bool(rollout),
    }
    ready = (
        not rollout
        and details["proxyGroupReady"]
        and details["observedGeneration"] >= details["generation"]
        and details["currentRevision"] == target_revision
        and details["updatedReplicas"] == replicas
        and details["readyReplicas"] == replicas
        and details["availableReplicas"] == replicas
        and details["podsOnRevision"] == replicas
        and details["podsReadyOnRevision"] == replicas
    )
    return ready, details, pods


def delete_proxy_pod(pod):
    name = pod["metadata"]["name"]
    path = f"/api/v1/namespaces/{PROXY_NS}/pods/{urllib.parse.quote(name, safe='')}"
    kube(path, "DELETE")
    print(f"deleted ProxyGroup pod {PROXY_NS}/{name}; waiting for replacement", flush=True)


def restart_operator():
    path = f"/apis/apps/v1/namespaces/{PROXY_NS}/deployments/{urllib.parse.quote(OPERATOR_NAME, safe='')}"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    kube(path, "PATCH", {"spec": {"template": {"metadata": {"annotations": {"ts-vip-watchdog/restarted-at": stamp}}}}})
    print(f"restarted Tailscale operator {PROXY_NS}/{OPERATOR_NAME} for VIP reconciliation", flush=True)


def progress_proxy_rollout(proxy_group):
    rollout = rollouts.get(proxy_group)
    if not rollout:
        return True
    path = f"/apis/apps/v1/namespaces/{PROXY_NS}/statefulsets/{urllib.parse.quote(proxy_group, safe='')}"
    _, sts = kube(path)
    status = sts.get("status") or {}
    if status.get("updateRevision") != rollout["target_revision"]:
        print(f"aborting {proxy_group} pod rollout: StatefulSet revision changed from {rollout['target_revision']} to {status.get('updateRevision')}", flush=True)
        rollouts.pop(proxy_group, None)
        return False
    pods = proxy_pods(sts)
    by_name = {pod.get("metadata", {}).get("name"): pod for pod in pods}
    waiting_name = rollout.get("waiting_name")
    if waiting_name:
        replacement = by_name.get(waiting_name)
        if not replacement or replacement.get("metadata", {}).get("uid") == rollout["old_uid"] or not pod_ready(replacement):
            return False
        if replacement.get("metadata", {}).get("labels", {}).get("controller-revision-hash") != rollout["target_revision"] or not proxy_group_ready(proxy_group):
            return False
        rollout["waiting_name"] = None
        rollout["old_uid"] = None
        print(f"ProxyGroup pod {PROXY_NS}/{waiting_name} replacement is Ready", flush=True)
    if rollout["remaining"]:
        if any(not pod_ready(pod) for pod in pods):
            return False
        next_name = rollout["remaining"].pop(0)
        next_pod = by_name.get(next_name)
        if not next_pod:
            return False
        rollout["waiting_name"] = next_name
        rollout["old_uid"] = next_pod.get("metadata", {}).get("uid")
        delete_proxy_pod(next_pod)
        return False
    print(f"ProxyGroup pod rollout complete for {PROXY_NS}/{proxy_group}", flush=True)
    rollouts.pop(proxy_group, None)
    return True


def proxy_rollout_ready(proxy_group):
    ready, _, _ = proxy_rollout_status(proxy_group)
    return ready


def restart_proxy(proxy_group):
    if proxy_group in rollouts:
        progress_proxy_rollout(proxy_group)
        return False
    ready, details, pods = proxy_rollout_status(proxy_group)
    if not ready:
        print(
            f"skipping ProxyGroup restart {PROXY_NS}/{proxy_group}: rollout still in progress "
            f"pods={details['podsReadyOnRevision']}/{details['replicas']} "
            f"updated={details['updatedReplicas']}/{details['replicas']} "
            f"ready={details['readyReplicas']}/{details['replicas']} "
            f"available={details['availableReplicas']}/{details['replicas']}",
            flush=True,
        )
        return False
    ordered = sorted(pods, key=pod_ordinal, reverse=True)
    if len(ordered) != details["replicas"]:
        print(f"skipping ProxyGroup restart {PROXY_NS}/{proxy_group}: found {len(ordered)}/{details['replicas']} pods", flush=True)
        return False
    first = ordered.pop(0)
    rollouts[proxy_group] = {
        "target_revision": details["targetRevision"],
        "remaining": [pod["metadata"]["name"] for pod in ordered],
        "waiting_name": first["metadata"]["name"],
        "old_uid": first["metadata"].get("uid"),
    }
    delete_proxy_pod(first)
    return True


def tailscale_access_token():
    client_id = os.environ["TAILSCALE_CLIENT_ID"]
    client_secret = os.environ["TAILSCALE_CLIENT_SECRET"]
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request("https://api.tailscale.com/api/v2/oauth/token", data=body, headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp)["access_token"]


def tailscale_vip_services(access):
    req = urllib.request.Request("https://api.tailscale.com/api/v2/tailnet/-/vip-services", headers={"Authorization": f"Bearer {access}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.load(resp).get("vipServices") or []


def delete_vip_for_ip(ip):
    access = tailscale_access_token()
    vip_services = tailscale_vip_services(access)
    match = next((svc for svc in vip_services if ip in svc.get("addrs", [])), None)
    if not match:
        raise RuntimeError(f"no Tailscale VIP service found for {ip}")
    service_name = match["name"]
    name = urllib.parse.quote(service_name, safe="")
    req = urllib.request.Request(f"https://api.tailscale.com/api/v2/tailnet/-/vip-services/{name}", headers={"Authorization": f"Bearer {access}"}, method="DELETE")
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"deleted stale Tailscale VIP {service_name} for {ip}: HTTP {resp.status}", flush=True)
    return service_name


def wait_for_vip_recreation(service_name):
    deadline = time.time() + VIP_RECREATE_WAIT
    gone = False
    while time.time() < deadline:
        access = tailscale_access_token()
        names = {svc.get("name") for svc in tailscale_vip_services(access)}
        if service_name not in names:
            gone = True
        elif gone:
            print(f"Tailscale VIP {service_name} recreated; waiting {VIP_RECREATE_SETTLE}s for operator reconciliation", flush=True)
            time.sleep(VIP_RECREATE_SETTLE)
            return
        time.sleep(5)
    raise RuntimeError(f"Tailscale VIP {service_name} was not observed to be recreated")


# key -> {failures, stage, repair_at, cooldown_until, endpoint_fingerprint};
# stage 0 normal, 1 restarted, 2 VIP reset.
state = {}
# proxy group -> pod-by-pod rollout state.
rollouts = {}
# Tailscale ProxyGroup pods do not reliably reload AdvertiseServices after
# operator config or backend changes. Force one clean reconciliation at startup,
# then roll only the affected ProxyGroup when Services or EndpointSlices change.
startup_reconciled = False
last_service_sets = None
print("watching all Tailscale LoadBalancer Services", flush=True)
while True:
    try:
        endpoint_counts, endpoint_fingerprints = endpoints_by_service()
        proxy_groups = ha_proxy_groups()
        for proxy_group in sorted(set(rollouts).intersection(proxy_groups)):
            progress_proxy_rollout(proxy_group)
        if not startup_reconciled:
            startup_complete = True
            for proxy_group in sorted(proxy_groups):
                if not restart_proxy(proxy_group):
                    startup_complete = False
            if startup_complete:
                startup_reconciled = True
                print("startup ProxyGroup reconciliation complete", flush=True)
        endpoint_changed_groups = set()
        service_list = services(proxy_groups)
        current_service_sets = {proxy_group: set() for proxy_group in proxy_groups}
        for service in service_list:
            meta = service["metadata"]
            key = f"{meta.get('namespace')}/{meta.get('name')}"
            proxy_group = meta.get("annotations", {}).get("tailscale.com/proxy-group")
            current_service_sets.setdefault(proxy_group, set()).add(key)
        if last_service_sets is not None:
            for proxy_group in proxy_groups:
                if last_service_sets.get(proxy_group, set()) != current_service_sets.get(proxy_group, set()):
                    endpoint_changed_groups.add(proxy_group)
                    print(f"{proxy_group} Tailscale Service set changed; scheduling ProxyGroup restart", flush=True)
        last_service_sets = current_service_sets
        for service in service_list:
            meta = service["metadata"]
            key = f"{meta.get('namespace')}/{meta.get('name')}"
            proxy_group = meta.get("annotations", {}).get("tailscale.com/proxy-group")
            ips = vip_ips(service)
            if not proxy_group or not ips:
                continue
            item = state.setdefault(key, {"failures": 0, "stage": 0, "repair_at": 0, "cooldown_until": 0, "endpoint_fingerprint": None})
            endpoint_fingerprint = endpoint_fingerprints.get((meta.get("namespace"), meta.get("name")), "")
            if item["endpoint_fingerprint"] is not None and item["endpoint_fingerprint"] != endpoint_fingerprint:
                endpoint_changed_groups.add(proxy_group)
                print(f"{key} EndpointSlices changed; scheduling ProxyGroup restart", flush=True)
            item["endpoint_fingerprint"] = endpoint_fingerprint
            ok, ready = service_healthy(service, endpoint_counts)
            print(f"{key} vip={','.join(ips)} proxy={proxy_group} health={'ok' if ok else 'FAIL'} ready={ready} stage={item['stage']}", flush=True)
            now = time.time()
            if ok:
                item.update(failures=0, stage=0, repair_at=0)
                continue
            item["failures"] += 1
            if item["stage"] == 2:
                if proxy_group in rollouts:
                    continue
                if now < item["cooldown_until"]:
                    continue
                print(f"post-repair health still failing for {key}; returning to staged recovery", flush=True)
                item.update(failures=0, stage=0, cooldown_until=0, repair_at=0)
                continue
            if now < item["cooldown_until"]:
                continue
            if item["failures"] >= FAILURES_BEFORE_REPAIR and item["stage"] == 0:
                if restart_proxy(proxy_group):
                    item.update(stage=1, repair_at=now + RESTART_GRACE)
            elif item["stage"] == 1 and now >= item["repair_at"]:
                if not proxy_rollout_ready(proxy_group):
                    print(f"deferring VIP repair for {key}: ProxyGroup rollout still in progress", flush=True)
                    item["repair_at"] = now + REPAIR_RETRY
                    continue
                deleted_all = True
                recreated_names = set()
                for ip in ips:
                    try:
                        recreated_names.add(delete_vip_for_ip(ip))
                    except Exception as exc:
                        deleted_all = False
                        print(f"VIP deletion failed for {key} ({ip}): {type(exc).__name__}: {exc}", flush=True)
                if not deleted_all:
                    item["repair_at"] = now + REPAIR_RETRY
                    continue
                try:
                    restart_operator()
                    for service_name in recreated_names:
                        wait_for_vip_recreation(service_name)
                except Exception as exc:
                    print(f"VIP recreation wait failed for {key}: {type(exc).__name__}: {exc}", flush=True)
                    item["repair_at"] = now + REPAIR_RETRY
                    continue
                if restart_proxy(proxy_group):
                    item.update(stage=2, cooldown_until=time.time() + POST_REPAIR_GRACE)
                else:
                    print(f"deferring post-repair ProxyGroup restart for {key}: rollout still in progress", flush=True)
                    item["repair_at"] = time.time() + REPAIR_RETRY
        for proxy_group in sorted(endpoint_changed_groups):
            restart_proxy(proxy_group)
    except Exception as exc:
        print(f"watchdog error: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
    time.sleep(INTERVAL)
