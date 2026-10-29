#!/usr/bin/env python3
"""End-to-end watchdog for Tailscale Kubernetes VIP Services."""
import base64
import json
import os
import socket
import ssl
import time
import traceback
import urllib.parse
import urllib.request

PROXY_NS = os.environ.get("PROXY_NS", "tailscale")
FAILURES_BEFORE_REPAIR = int(os.environ.get("FAILURES_BEFORE_REPAIR", "3"))
RESTART_GRACE = int(os.environ.get("RESTART_GRACE", "180"))
COOLDOWN = int(os.environ.get("COOLDOWN", "1800"))
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
    result = {}
    for sl in (data.get("items") or []):
        labels = sl.get("metadata", {}).get("labels", {})
        name = labels.get("kubernetes.io/service-name")
        namespace = sl.get("metadata", {}).get("namespace")
        if not name:
            continue
        key = (namespace, name)
        endpoints = sl.get("endpoints") or []
        result[key] = result.get(key, 0) + sum(1 for ep in endpoints if ep.get("conditions", {}).get("ready") is True)
    return result


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


def restart_proxy(proxy_group):
    path = f"/apis/apps/v1/namespaces/{PROXY_NS}/statefulsets/{urllib.parse.quote(proxy_group, safe='')}"
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    kube(path, "PATCH", {"spec": {"template": {"metadata": {"annotations": {"ts-vip-watchdog/restarted-at": stamp}}}}})
    print(f"restarted ProxyGroup StatefulSet {PROXY_NS}/{proxy_group}", flush=True)


def delete_vip_for_ip(ip):
    client_id = os.environ["TAILSCALE_CLIENT_ID"]
    client_secret = os.environ["TAILSCALE_CLIENT_SECRET"]
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request("https://api.tailscale.com/api/v2/oauth/token", data=body, headers={"Authorization": f"Basic {basic}", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        access = json.load(resp)["access_token"]
    req = urllib.request.Request("https://api.tailscale.com/api/v2/tailnet/-/vip-services", headers={"Authorization": f"Bearer {access}"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        vip_services = (json.load(resp).get("vipServices") or [])
    match = next((svc for svc in vip_services if ip in svc.get("addrs", [])), None)
    if not match:
        raise RuntimeError(f"no Tailscale VIP service found for {ip}")
    name = urllib.parse.quote(match["name"], safe="")
    req = urllib.request.Request(f"https://api.tailscale.com/api/v2/tailnet/-/vip-services/{name}", headers={"Authorization": f"Bearer {access}"}, method="DELETE")
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"deleted stale Tailscale VIP {match['name']} for {ip}: HTTP {resp.status}", flush=True)


# key -> {failures, stage, repair_at, cooldown_until}; stage 0 normal, 1 restarted, 2 VIP reset.
state = {}
print("watching all Tailscale LoadBalancer Services", flush=True)
while True:
    try:
        endpoint_counts = endpoints_by_service()
        proxy_groups = ha_proxy_groups()
        for service in services(proxy_groups):
            meta = service["metadata"]
            key = f"{meta.get('namespace')}/{meta.get('name')}"
            proxy_group = meta.get("annotations", {}).get("tailscale.com/proxy-group")
            ips = vip_ips(service)
            if not proxy_group or not ips:
                continue
            item = state.setdefault(key, {"failures": 0, "stage": 0, "repair_at": 0, "cooldown_until": 0})
            ok, ready = service_healthy(service, endpoint_counts)
            print(f"{key} vip={','.join(ips)} proxy={proxy_group} health={'ok' if ok else 'FAIL'} ready={ready} stage={item['stage']}", flush=True)
            now = time.time()
            if ok:
                item.update(failures=0, stage=0, repair_at=0)
                continue
            item["failures"] += 1
            if now < item["cooldown_until"]:
                continue
            if item["failures"] >= FAILURES_BEFORE_REPAIR and item["stage"] == 0:
                restart_proxy(proxy_group)
                item.update(stage=1, repair_at=now + RESTART_GRACE)
            elif item["stage"] == 1 and now >= item["repair_at"]:
                for ip in ips:
                    delete_vip_for_ip(ip)
                restart_proxy(proxy_group)
                item.update(stage=2, cooldown_until=now + COOLDOWN)
    except Exception as exc:
        print(f"watchdog error: {type(exc).__name__}: {exc}", flush=True)
        traceback.print_exc()
    time.sleep(INTERVAL)
