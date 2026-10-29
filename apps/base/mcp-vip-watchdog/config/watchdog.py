#!/usr/bin/env python3
import base64
import json
import os
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

VIP_IP = os.environ.get("VIP_IP", "100.64.72.152")
VIP_URL = os.environ.get("VIP_URL", f"http://{VIP_IP}/sse")
TAILNET = os.environ.get("TAILNET", "-")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "svc:mcp-system-mcp-lb-mc")
SERVICE_NS = os.environ.get("SERVICE_NS", "mcp-system")
SERVICE = os.environ.get("SERVICE", "mcp-lb-mc")
PROXY_NS = os.environ.get("PROXY_NS", "tailscale")
PROXY_STS = os.environ.get("PROXY_STS", "mc-ingress-proxy")
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
    with urllib.request.urlopen(req, timeout=10, context=context or (SSL if url.startswith(KUBE_BASE) else None)) as resp:
        raw = resp.read()
        if not url.startswith(KUBE_BASE):
            return resp.status, raw.decode(errors="replace")
        return resp.status, json.loads(raw) if raw else None


def kube(path, method="GET", body=None):
    return request(KUBE_BASE + path, method, body)


def ready_backends():
    _, data = kube(f"/apis/discovery.k8s.io/v1/namespaces/{SERVICE_NS}/endpointslices?labelSelector=" + urllib.parse.quote(f"kubernetes.io/service-name={SERVICE}"))
    return sum(1 for sl in data.get("items", []) for ep in sl.get("endpoints", []) if ep.get("conditions", {}).get("ready") is True)


def probe():
    try:
        status, body = request(VIP_URL, headers={"Accept": "text/event-stream"})
        return status == 200 and "event: endpoint" in (body or "")
    except Exception as exc:
        print(f"probe failed: {type(exc).__name__}: {exc}", flush=True)
        return False


def restart_proxy():
    stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path = f"/apis/apps/v1/namespaces/{PROXY_NS}/statefulsets/{PROXY_STS}"
    kube(path, "PATCH", {"spec": {"template": {"metadata": {"annotations": {"mcp-watchdog/restarted-at": stamp}}}}})
    print(f"restarted {PROXY_NS}/{PROXY_STS}", flush=True)


def delete_vip_service():
    client_id = os.environ["TAILSCALE_CLIENT_ID"]
    client_secret = os.environ["TAILSCALE_CLIENT_SECRET"]
    token = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    body = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
    req = urllib.request.Request("https://api.tailscale.com/api/v2/oauth/token", data=body, headers={"Authorization": f"Basic {token}", "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        access = json.load(resp)["access_token"]
    name = urllib.parse.quote(SERVICE_NAME, safe="")
    req = urllib.request.Request(f"https://api.tailscale.com/api/v2/tailnet/{urllib.parse.quote(TAILNET, safe='')}/vip-services/{name}", headers={"Authorization": f"Bearer {access}"}, method="DELETE")
    with urllib.request.urlopen(req, timeout=15) as resp:
        print(f"deleted Tailscale VIP service {SERVICE_NAME}: HTTP {resp.status}", flush=True)


failures = 0
stage = 0
repair_at = 0
cooldown_until = 0
print(f"watching {VIP_URL} with {FAILURES_BEFORE_REPAIR} failures before repair", flush=True)
while True:
    now = time.time()
    try:
        backends = ready_backends()
        ok = backends > 0 and probe()
        print(f"health={'ok' if ok else 'FAIL'} ready_backends={backends} stage={stage}", flush=True)
        if ok:
            failures = 0
            stage = 0
            repair_at = 0
        else:
            failures += 1
            if now < cooldown_until:
                pass
            elif failures >= FAILURES_BEFORE_REPAIR and stage == 0:
                restart_proxy()
                stage = 1
                repair_at = now + RESTART_GRACE
            elif stage == 1 and now >= repair_at:
                delete_vip_service()
                restart_proxy()
                stage = 2
                cooldown_until = now + COOLDOWN
    except Exception as exc:
        print(f"watchdog error: {type(exc).__name__}: {exc}", flush=True)
    time.sleep(INTERVAL)
