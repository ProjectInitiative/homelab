# OpenBao LLM/MCP Secrets Upgrade

**Problem:** MCP properly restricts secrets at the K8s API level, but LLMs still try to use local dev configs and can sometimes read secrets for manual ops. We should never need to do that — we have OpenBao.

## 1. Programmatic OpenBao Configuration

Currently everything (engines, users, roles, permissions) is done manually via the web UI.

- [ ] **Research tooling**: Evaluate Terraform provider, CLI (`bao`), REST API, VSO CRDs, or a custom operator for declaring OpenBao config as code
- [ ] **Policy-as-code in `apps.yaml`**: Embed OpenBao policy definitions alongside `vaultSecrets` in the app catalog, so the cdk8s generator produces both K8s CRDs *and* Vault config in one shot

## 2. LLM-Specific Roles & Permissions

- [ ] **`read-secret-metadata` role**: Can lookup paths, describe metadata, check existence — but never read data values
- [ ] **`create-secret` role**: Can write new secrets to Vault paths scoped to K8s operations
- [ ] **Neither role grants `read` on data paths** — no secret value ever leaves Vault to an LLM

## 3. Dynamic Secrets Over Static Where Possible

- [ ] Swap `VaultStaticSecret` for `VaultDynamicSecret` / `VaultPKISecret` for Postgres creds, TLS certs, etc.
- [ ] Benefits: auto-rotation, short TTLs, and LLM roles never touch the values (the VSO handles the lifecycle)

## 4. Secret Lifecycle Tied to App Lifecycle

- [ ] **App add → provision secrets**: When an app with `vaultSecrets` is added to a cluster, programmatically create the Vault path, role binding, and policy
- [ ] **App remove → revoke secrets**: When an app is removed from `clusters/*.yaml`, revoke its Vault secret paths and delete role bindings — no orphaned secrets

## 5. Drift Detection & Reconciliation

- [ ] **CI/CD drift check**: Compare declared `VaultStaticSecret` specs in `apps.yaml` / `clusters/*.yaml` against what actually lives in Vault. Warn if paths were manually tampered with or deleted.
- [ ] **VaultAuth ↔ OpenBao role reconciler**: Periodically ensure every cdk8s-generated `VaultAuth` has a matching OpenBao Kubernetes auth role, correctly scoped. Delete orphans.

## 6. Hard Enforcement at the LLM Boundary

- [ ] **Pre-flight proxy or hook**: Before an LLM runs a command touching secret-like content (`.env`, `kubectl get secret`, `~/.kube/config`, etc.), intercept and redirect to OpenBao
- [ ] **Short-lived scoped tokens**: Each LLM session gets an OpenBao token with a 5–15 min TTL and explicit path restrictions — no long-lived credentials for agents
- [ ] **Audit-only read role**: A dedicated role that logs *all* access attempts (especially reads) to a separate audit sink, flagging any bypass attempts

## 7. Agent Instructions & Guardrails

- [ ] Update AGENTS.md / MCP agent instructions to route all secret operations exclusively through OpenBao
- [ ] Add explicit guardrails preventing LLMs from reading local dev config files for secret material
