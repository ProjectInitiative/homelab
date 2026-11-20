# ADR: child Application health does NOT gate parent sync (removed 2026-11-20)

## Decision

Removed `patch-argocd-cm-application-health.yaml` — the custom
`argoproj.io/Application` health check in argocd-cm. Argo CD's default
(since v1.8, issue #3781) is restored: a parent Application does NOT
health-gate on its children.

## Why the customization existed (and why both forms failed)

2026-11-17: homelab-root waited for the glm53-flash lane's workload health
while the lane needed a blocked controller roll — genuine deadlock, so a
custom health check was added gating on the child's *sync outcome*
(operationState Failed/Error → Degraded). That re-created the same
deadlock class in a different form: a child's failed sync op is STICKY
(operationState persists until a new op runs; a Synced child never runs a
new op), so one failed sync marked the child Degraded to the parent
forever. 2026-11-20: ai-proxy (failed Replace-cascade op) and
karmada-operator (failed CC sync) froze homelab-root at wave gating for
hours; three rounds of fixes (#401–#403) sat unapplied because the parent
op could never complete — the fix for the deadlock was blocked BY the
deadlock.

## Resulting behavior

- Parent ops apply children in wave order; child Applications are
  Healthy-as-created, so waves proceed without waiting on child workloads.
- Wave annotations retain their ordering role (CRDs before consumers etc.)
  but no longer gate on runtime health.
- Child workload health remains fully visible in each child Application.
- The per-child `SkipHealthCheck=true` / `ignore-healthcheck` annotations
  (PRs #400/#401/#404) become redundant no-ops; strip in cleanup.
- homelab-root keeps its retry policy (PR404); ops can still fail on
  transient API errors and now retry to completion.

## References

- Argo default: argo-cd#3781 (Application health removed from defaults, v1.8)
- Akuity "Application Dependencies with Argo CD" — all wave-gating patterns
  require re-enabling this health check; without it, app-of-apps orders
  without gating
- Keel: OQ-0058 (root restructure), RISK-0056 addendum (same-day incidents)
