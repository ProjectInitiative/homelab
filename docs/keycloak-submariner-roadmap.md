# Cascading Roadmap: Interconnect → Identity → Relay → Storage → Workloads

> One long-term vision: two clusters (mc/juicefs + workload, cc/control + public),
> joined by Submariner, with Keycloak as the single identity source, a public
> relay on cc's public nodes, shared JuiceFS-backed storage, and finally dev VMs.
>
> **Cardinal rule of every phase:** kill hardcoded Tailscale IPs. They are the #1
> recurring cause of breakage (see TODO.md). Every cross-cluster endpoint gets a
> stable DNS name + a resolvable service. Submariner unlocks the *routing*, but
> DNS naming is what makes it durable.

---
## Dependencies at a glance

```
Submariner (0) ──► public relay (2) ─┐
      │                              ├──► workloads/dev VMs (4)
      └──► Keycloak+PG (1) ──────────┤
                    │                │
                    └──► Samba storage (3) ──┘
```
- (0) is the lynchpin: nothing cross-cluster works without it.
- (1) Keycloak+PG are **cc-only**, so they don't strictly need (0) to come up — but
  they need a *stable reachable identity endpoint* for (3) and (4) on mc.
- (2) needs (0) to route external traffic to workload services.
- (3) needs (0) **and** (1) (Samba on mc binds to Keycloak on cc).
- (4) needs (0), (1), (3).

---

## Phase 0 — Foundation: Cluster interconnect  *(MUST go first)*

### 0.1 Finish the Submariner mesh (mc ↔ cc)
- [ ] Confirm Submariner operator installed & healthy on **both** mc and cc
- [ ] Broker on cc reachable from mc — replace hardcoded `brokerK8sApiServer: "https://100.95.205.21:443"` (clusters/mc.yaml:148) with a **stable DNS name** (in-cluster svc or MagicDNS) before/while finishing
- [ ] Verify gateways (mode active/passive) for mc + cc
- [ ] Validate east-west: `kubectl --context cc` can reach an mc service via clusterServiceIP, and vice-versa
- [ ] **Smoke test:** a Service on mc resolved from cc by DNS (not raw IP)

### 0.2 Stable DNS across clusters (kills Tailscale-IP rot)
- [ ] Wire the existing Tailscale DNS / in-cluster resolution so cross-cluster services resolve by FQDN
- [ ] Migrate remaining hardcoded IPs off Tailscale:
  - `bootstrap/base/openbao-auth-config/config/vault-connection.yaml` (OpenBao addr)
  - `grafana-alloy` Loki/Mimir push URLs (apps.yaml:326,347)
  - `submariner-operator` broker URL
- [ ] Add a guardrail note in AGENTS.md: "no hardcoded Tailscale IPs for cross-cluster refs — use DNS"

**Priority: P0. Blocks 0? no — but blocks (2), (3), (4). Can start (1) in parallel.**

---

### 0.3 Nebula migration *(breaks the Tailscale→Nebula circular dependency)*

**Goal:** replace Tailscale with Nebula (PSK/CA from OpenBao), self-hosted controller, without a chicken-and-egg (lighthouses are cc public VPSes; OpenBao is reachable only via Tailscale today).

**Principle:** the lighthouses need OpenBao **once at provisioning**, not at runtime. Provision out-of-band over a channel that exists now; Nebula carries traffic afterward.

- [ ] **Decide cert model.** Nebula certs are custom (`nebula-cert ca`/`sign`) — store CA key, CA cert, PSK, and per-host cert/key in **OpenBao KV**, and use OpenBao RBAC + audit for who can read them. (True X.509 PKI signing from Vault is orthogonal / later.)
- [ ] **Stand up the OpenBao side**: KV paths for `nebula/psk`, `nebula/ca`, `nebula/hosts/<host>`, plus an RBAC policy so only provisioning hops can read them.
- [ ] **Bootstrap lighthouses via existing channel** (Tailscale or SSH from workstation): first-boot step pulls PSK+CA+host cert/key from OpenBao, writes `config.yml`, one-time. Lighthouse offline from OpenBao after.
- [ ] **Run Tailscale as control plane during migration** — keep it up as the management channel; Nebula is the data plane. Overlays coexist; don't rip Tailscale until all hosts migrated + validated.
- [ ] **Migrate hosts** (workstation, kubevirt dev VMs later) one by one; each provisioned via the control plane, then joins the mesh.
- [ ] **Automated enrollment (optional, later):** expose a restricted OpenBao issuer via the **cc public relay** (Phase 2) over HTTPS so any host can fetch certs without Tailscale.
- [ ] **Decommission Tailscale** only after: all hosts migrated, Nebula mesh validated, and (if used) the relay issuer is live as a second control path.

**Priority: P0.5. Depends on (0) only loosely; breaks the Tailscale dependency and unblocks hosts working without Tailscale.**

---

## Phase 1 — Identity: Keycloak + Postgres on cc  *(cc-only, parallel-safe with 0)*

### 1.1 Provision Postgres on cc
- [ ] Reuse the existing CNPG pattern (`bootstrap/base/cnpg/database`) on cc
- [ ] Dedicated DB + user for Keycloak (via CNPG role/user), creds in OpenBao → VaultStaticSecret
- [ ] Point cnpg at cc-local storage (local-path or JuiceFS if it's ever on cc; otherwise local-path for now)

### 1.2 Deploy Keycloak on cc
- [ ] Helm chart (keycloak/keycloak) with `db.vendor=postgres` → CNPG endpoint
- [ ] Configure in-cluster TLS (step-ca already in repo) for the Keycloak URL
- [ ] Set `argocd.argoproj.io/sync-wave` after postgres; enable SSA + CreateNamespace
- [ ] Storage: Keycloak needs a small volume for theming/caches — use local-path (ephemeral-ish) on cc, not JuiceFS (which lives on mc)
- [ ] **HA note:** Keycloak itself is stateless-ish; run 2+ replicas behind a Service. Cache uses `infinispan`.

### 1.3 Expose / announce Keycloak
- [ ] Internal Service (ClusterIP) so mc workloads can resolve `keycloak.keycloak.svc...`
- [ ] Public/gateway route once (2) is up; until then keep internal + one stable URL for auth
- [ ] Register the Keycloak URL in the cross-cluster DNS service from 0.2

### 1.4 Identity model
- [ ] Create a realm (e.g., `homelab`)
- [ ] Create groups for the silos you'll need in storage (e.g. `storage-users`, `storage-admins`, per-app groups)
- [ ] Set up user federation source later (LDAP/OpenLDAP or direct users) — decide user storage strategy
- [ ] Register clients for: shared-storage Samba (LDAP bind via Keycloak's LDAP/AD option), and future web apps

**Priority: P1. Depends on: none hard, but benefits from (0.2) for stable endpoints.**
**Blocking: (3) needs (1).**

---

## Phase 2 — Public relay: Submariner → cc public nodes *(replaces Tailscale funnel)*

### 2.1 Routing baseline
- [ ] Confirm Submariner gateway routing of external traffic to the cc public node(s)
- [ ] Verify a workload service is reachable from the public internet via cc's public IPs (through the mesh)

### 2.2 Ingress + relay on cc public nodes
- [ ] Deploy ingress (Istio or nginx-ingress) on cc with the public node(s) as the entry
- [ ] Point the existing `mc-ingress-proxy`/Tailscale proxy-group workloads to the cc relay instead of Tailscale funnel

### 2.3 Migration
- [ ] Enumerate current Tailscale-funnel-exposed apps (temp-egress, dnsutils, docker-registry, mcp-kubernetes, etc.)
- [ ] Migrate each to the cc public relay; cut over DNS
- [ ] Keep Tailscale as fallback during cutover, decommission funnels after

**Priority: P2. Depends on (0) strongly. Unblocks public Keycloak (1.3) and lets (4) expose to LAN.**

---

## Phase 3 — Shared storage: Samba gateway over JuiceFS on mc

### 3.1 JuiceFS-backed gateway (single replica first)
- [ ] RWX PVC on `juicefs-sc` for the shared store
- [ ] Samba Deployment/StatefulSet (1 replica), PVC mounted at `/jfs`, `ea support = yes`
- [ ] `smb.conf` via ConfigMap; one share per silo
- [ ] Service `type: LoadBalancer` (or Tailscale/relay pattern), TCP 445
- [ ] **Local users first** to validate, OR jump straight to (3.2)

### 3.2 Wire Samba → Keycloak (via Submariner)  ← the real goal
- [ ] Samba on **mc** binds to Keycloak on **cc** through the Submariner mesh (mc→cc)
  - Two options: Samba joins a Keycloak/AD-managed identity, or binds to an LDAP interface
  - (Keycloak is the IdP; use its LDAP/AD-vendor endpoint or federate an OpenLDAP that Samba talks to)
- [ ] Centralized users so N replicas share auth consistently
- [ ] Per-user/group **silos = POSIX ACLs** (`setfacl`) stored as JuiceFS xattrs → shared across replicas & restarts

### 3.3 Scale out (HA)
- [ ] Bump Samba replicas to N (stateless) behind one LB endpoint
- [ ] Add `sessionAffinity: ClientIP` on the Service
- [ ] JuiceFS mount options for Samba: `--no-posix-lock --no-bsd-lock` (tuned via the CSI node config / mount options)
- [ ] Note the locking tradeoff: byte-range locks become per-replica; acceptable for "dump files" workloads

**Priority: P3. Depends on (0) AND (1).**

---

## Phase 4 — Workloads + Dev VMs

- [ ] kubevirt dev VMs (kubevirt already in repo) with:
  - [ ] Identity via Keycloak (OIDC/LDAP) — from (1)
  - [ ] Shared storage from Samba/JuiceFS gateway — from (3)
  - [ ] Public access via cc relay — from (2)
- [ ] New services on mc/cc get a Keycloak client by convention (document it)
- [ ] CI/deploy pipeline treats Keycloak brokers + LB endpoints as DNS, never raw IPs

**Priority: P4. Depends on (0), (1), (2), (3).**

---

## Cross-cutting concerns (enabled as you go)

- **Secrets/provisioning:** Keycloak + PG creds (and any new DBs) go through OpenBao → VaultStaticSecret, matching the existing `vaultSecrets` abstraction (todo.md is the OpenBao programmatic-config work — worth doing before many new apps land).
- **DNS-first everywhere:** the recurring "Tailscale IP rot" list (TODO.md) is the template; adopt a rule that every new cross-cluster app uses a DNS name.
- **Ingress/TLS:** step-ca is already in repo; use it for Keycloak + relay certs.

## Suggested execution order (what I'd do first, this week)
1. **0.1** — finish Submariner, fix the broker DNS. (unblocks everything)
2. **0.2** — fix the 3 known hardcoded IPs. (cheap, high value)
3. **1.1 + 1.2** — CNPG Postgres + Keycloak on cc. (parallel-safe, independent of mc)
4. Then choose: (2) public relay, or (3) shared storage — storage is lower-risk and gives you a concrete win; relay is needed before you drop Tailscale funnels.
