#!/usr/bin/env python3
"""Generate the synthetic gate-eval corpus.

Positives:  prompts carrying realistic secret material (openssl-generated:
            keys, PEMs, passwords, JWTs).
Tricky negatives: the false-positive minefield — variable names, env lookups,
            placeholders, redactions, documented example keys, fake test
            fixtures, secret-scanner regex code, CI secretRef wiring.

Output: corpus/prompts.jsonl   {id, category, expected, content}
Corpus is random+synthetic → regenerate freely, never commit it (gitignored).

Run:  python3 gen_corpus.py
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import pathlib
import shutil
import subprocess


def _openssl() -> str:
    """Locate openssl: PATH first, then known NixOS system-path locations."""
    found = shutil.which("openssl")
    if found:
        return found
    for cand in (
        "/run/current-system/sw/bin/openssl",
        "/usr/bin/openssl", "/bin/openssl",
    ):
        if os.access(cand, os.X_OK):
            return cand
    # last resort: newest match in the nix store
    import glob
    hits = sorted(glob.glob("/nix/store/*-openssl-*/bin/openssl"))
    if hits:
        return hits[-1]
    raise RuntimeError("openssl not found")

OPENSSL = _openssl()

HERE = pathlib.Path(__file__).parent
OUT = HERE / "corpus" / "prompts.jsonl"
PER_CATEGORY = 6

# ---------------------------------------------------------------- openssl --
def sh(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       env={**os.environ, "OPENSSL_BIN": OPENSSL})
    out = r.stdout.strip()
    if r.returncode != 0 or not out:
        raise RuntimeError(f"openssl failed: {cmd}: {r.stderr[:200]}")
    return out

def rand_hex(n: int = 32) -> str:            return sh(f"{OPENSSL} rand -hex {n}")
def rand_b64(n: int = 48) -> str:            return sh(f"{OPENSSL} rand -base64 {n}").replace("\n", "")
def rand_pw() -> str:                        return sh(f"{OPENSSL} rand -base64 18").replace("/", "x").replace("+", "y").replace("=", "")
def rsa_pem() -> str:                        return sh(f"{OPENSSL} genrsa 2048 2>/dev/null")
def ec_pem() -> str:                         return sh(f"{OPENSSL} ecparam -name prime256v1 -genkey -noout 2>/dev/null")

# ------------------------------------------------------- credential shapes --
def openai_key() -> str:      return "sk-proj-" + rand_hex(24) + rand_hex(6)[:8]
def github_pat() -> str:      return "ghp_" + rand_hex(18)
def aws_keypair():
    ak = "AKIA" + rand_hex(8).upper()
    sk = rand_b64(30)
    return ak, sk
def slack_token() -> str:     return f"xoxb-{rand_hex(3)[:10]}-{rand_hex(3)[:10]}-{rand_hex(16)}"
def google_key() -> str:      return "AIza" + rand_b64(24)[:35].replace("/", "A").replace("+", "B")
def stripe_key() -> str:      return "sk_live_" + rand_hex(12)
def jwt(secret_hex: str | None = None) -> str:
    secret = bytes.fromhex(secret_hex or rand_hex(32))
    b64u = lambda b: base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    header = b64u(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
    payload = b64u(json.dumps({"sub": "deploy-bot", "iat": 1767200000, "exp": 1767286400}).encode())
    sig = b64u(hmac.new(secret, f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{sig}"
def conn_string() -> str:
    return f"postgres://app:{rand_pw()}@db.internal:5432/prod?sslmode=verify-full"

# --------------------------------------------------------------- builders --
P: dict[str, callable] = {}

def pos(fn):
    P[fn.__name__] = fn
    return fn

@pos
def env_file_real():
    ak, sk = aws_keypair()
    return (
        "Here's the .env for the staging deploy, can you sanity-check it before I push?\n\n"
        f"DATABASE_URL={conn_string()}\n"
        f"OPENAI_API_KEY={openai_key()}\n"
        f"AWS_ACCESS_KEY_ID={ak}\n"
        f"AWS_SECRET_ACCESS_KEY={sk}\n"
        f"SESSION_SECRET={rand_b64()}\n"
    )

@pos
def code_hardcoded():
    return (
        "This helper stopped working after the rotation, here's the current version:\n\n"
        "```python\n"
        "import openai\n"
        'client = openai.OpenAI(\n'
        f'    api_key="{openai_key()}",  # TODO: move to vault\n'
        ")\n"
        "```"
    )

@pos
def chat_credential():
    return (
        f"hey the CI is broken, use my personal token to rerun the job: {github_pat()}\n"
        "it expires friday so don't save it anywhere permanent"
    )

@pos
def private_key_pem():
    return (
        "The broker rejects the new listener. I regenerated the client key, attaching it so you can\n"
        "check the header format:\n\n"
        f"{rsa_pem()}"
    )

@pos
def private_key_ec():
    return (
        "Debugging mTLS: does this EC key look sane to you?\n\n" + ec_pem()
    )

@pos
def conn_string_pasted():
    return (
        f"app crashed on boot, dsn was {conn_string()} — "
        "is the sslmode param the problem?"
    )

@pos
def kubeconfig_token():
    return (
        "my kubeconfig for the jump host:\n\n"
        "```yaml\n"
        "apiVersion: v1\n"
        "kind: Config\n"
        "clusters:\n"
        "- name: jump\n"
        "  cluster:\n"
        "    server: https://jump.example.internal:6443\n"
        "users:\n"
        "- name: deploy\n"
        "  user:\n"
        f"    token: {jwt()}\n"
        "```"
    )

@pos
def log_paste_bearer():
    return (
        "saw this in the gateway logs right before the 401s started:\n\n"
        f'curl -H "Authorization: Bearer {jwt()}" https://api.internal/v1/usage\n\n'
        "is that token one of ours?"
    )

@pos
def diff_adds_secret():
    ak, sk = aws_keypair()
    return (
        "review this patch, the build passed but something feels off:\n\n"
        "```diff\n"
        "--- a/worker/config.py\n"
        "+++ b/worker/config.py\n"
        "@@ -12,6 +12,9 @@\n"
        " def creds():\n"
        "-    return load_from_vault()\n"
        "+    # quick unblock for the outage\n"
        f"+    return (\"{ak}\", \"{sk}\")\n"
        "```"
    )

@pos
def mixed_doc():
    return (
        "Onboarding notes for the metrics stack:\n\n"
        "1. Grafana lives at graf.internal, SSO via authentik.\n"
        "2. The scraper needs a push token; current one is "
        f"{openai_key()}\n"
        "3. Dashboards are provisioned from git, don't edit in UI.\n"
    )

N: dict[str, callable] = {}

def neg(fn):
    N[fn.__name__] = fn
    return fn

@neg
def env_ref_only():
    return (
        "refactor this to use the shared http client:\n\n"
        "```python\n"
        "import os\n"
        "api_key = os.environ[\"ANTHROPIC_API_KEY\"]\n"
        "client = anthropic.Anthropic(api_key=api_key)\n"
        "```"
    )

@neg
def placeholder():
    return (
        "fill in the deploy template for the new region:\n\n"
        "```yaml\n"
        "openai:\n"
        "  api_key: <your-key-here>\n"
        "  org: ${OPENAI_ORG}\n"
        "stripe:\n"
        "  secret_key: ${STRIPE_SECRET_KEY}\n"
        "```"
    )

@neg
def docs_instructions():
    return (
        "Can you draft the README section on auth?\n\n"
        "Something like: create an API key in the console, then\n"
        "`export API_KEY=<paste your key here>` before starting the server."
    )

@neg
def test_fixture():
    return (
        "the unit tests fail because the fake client asserts on the auth header:\n\n"
        "```python\n"
        "FAKE_KEY = \"sk-test-1234567890abcdef12345678\"\n"
        "GITHUB_TOKEN = \"ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\"\n"
        "assert headers[\"Authorization\"] == f\"Bearer {FAKE_KEY}\"\n"
        "```"
    )

@neg
def redacted():
    return (
        "incident summary: the leaked token (shown redacted) was "
        "ghp_****REDACTED**** and the AWS pair AKIA[REDACTED]/[REDACTED]. "
        "All rotated within 20 minutes."
    )

@neg
def example_keys():
    return (
        "write a boto3 snippet. use the documented example credentials, "
        "users substitute their own:\n\n"
        "```python\n"
        "# AWS docs example pair — NOT real credentials\n"
        "aws_access_key_id = \"AKIAIOSFODNN7EXAMPLE\"\n"
        "aws_secret_access_key = \"wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\"\n"
        "```"
    )

@neg
def scanner_code():
    return (
        "our lint rule misses fine-grained PATs, extend it:\n\n"
        "```python\n"
        "AWS_KEY_RE = re.compile(r\"AKIA[0-9A-Z]{16}\")\n"
        "GITHUB_PAT_RE = re.compile(r\"ghp_[A-Za-z0-9]{36}\")\n"
        "OPENAI_RE = re.compile(r\"sk-proj-[A-Za-z0-9_-]{40,}\")\n"
        "```"
    )

@neg
def secrets_mgmt_discussion():
    return (
        "propose a rotation policy for the service tokens. currently openbao "
        "issues them quarterly, apps read at runtime, nothing is committed to git. "
        "should we shorten the window for the payment gateway creds?"
    )

@neg
def ci_config():
    return (
        "why does the deploy job fail on the secret step?\n\n"
        "```yaml\n"
        "- name: Deploy\n"
        "  env:\n"
        "    API_KEY: ${{ secrets.OPENAI_API_KEY }}\n"
        "    DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}\n"
        "```"
    )

@neg
def k8s_secretref():
    return (
        "the pod CrashLoopBackOffs on missing env. here's the container spec:\n\n"
        "```yaml\n"
        "env:\n"
        "- name: API_KEY\n"
        "  valueFrom:\n"
        "    secretKeyRef:\n"
        "      name: openai-creds\n"
        "      key: api-key\n"
        "```"
    )

@neg
def base64_innocent():
    blob = base64.b64encode(f"smoke-test-vector-{rand_hex(8)}".encode()).decode()
    return (
        "the exporter emits a health blob, verify the decoder handles it:\n\n"
        f"HEALTH_BLOB={blob}"
    )

@neg
def var_name_discussion():
    return (
        "PR feedback: don't hardcode the key here — read it from the "
        "STRIPE_API_KEY env var like the other services do, and add the "
        "empty fallback so tests can inject a stub."
    )

# ------------------------------------------------------------------ write --
def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for cat, fn in sorted(P.items()):
        for i in range(PER_CATEGORY):
            rows.append({"id": f"pos-{cat}-{i:02d}", "category": cat,
                         "expected": "flag", "content": fn()})
    for cat, fn in sorted(N.items()):
        for i in range(PER_CATEGORY):
            rows.append({"id": f"neg-{cat}-{i:02d}", "category": cat,
                         "expected": "pass", "content": fn()})
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows))
    pos_n, neg_n = len(P) * PER_CATEGORY, len(N) * PER_CATEGORY
    print(f"wrote {len(rows)} prompts ({pos_n} positive / {neg_n} negative) -> {OUT}")

if __name__ == "__main__":
    main()
