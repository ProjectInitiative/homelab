# MiaAI upstream snapshot maintenance

`sync.py` maintains the GLM53 and DSV41 recipe provenance used by the existing
`llm-test/*-parity` lanes. It selectively copies reviewed Git blobs, records
SHA-256 checksums, generates a drift report, and validates safety invariants.
Vendored files are evidence only: current Kubernetes manifests do not execute or
mount this tree.

## Safety model

- `update` accepts only full 40-character commit SHAs, reads allowlisted blobs
  with `git --no-replace-objects show`, and never sources or runs upstream shell
  or Python. A supplied checkout's normalized `origin` must match the lock;
  runtime/vendor revisions must be ancestors of reviewed HEAD.
- `validate`, `drift`, and `check` are deterministic and network-free.
- No command invokes `kubectl`, applies resources, scales Deployments, builds or
  pulls an image, or contacts Kubernetes.
- Lane/vendor paths must be direct, contained, non-symlink paths. Serving
  resources remain separate, manually activated, and must validate with exact
  top-level Deployment `spec.replicas: 0` and worker-before-head ordering.
- Recipe, image, and model pins form an explicit compatibility bundle. Every
  `update` resets adoption to `pending-review`; integrity success is deliberately
  reported separately from `CURRENT` or `BLOCKED` runtime-adoption status.
- `update` refuses a dirty worktree unless a reviewer deliberately supplies
  `--force-dirty`; CI and normal updates should not use that override.

## Offline review commands

From the repository root:

```bash
# Verify full-SHA locks, vendored inventories/checksums, image/model pins,
# lane-specific settings, and zero serving replicas.
python3 hack/llm-upstream/sync.py validate --lane all

# Regenerate reports after an intentional lock/contract update.
python3 hack/llm-upstream/sync.py drift --lane all

# CI/review check: validate and fail if either generated drift.md is stale.
python3 hack/llm-upstream/sync.py check --lane all
# Equivalent report-only check:
python3 hack/llm-upstream/sync.py drift --lane all --check

python3 -m unittest discover -s hack/llm-upstream/tests -v
```

## Selective update commands (networked, never deploy)

A normal candidate update clones into a temporary directory, exports only the
paths already listed in that lane lock, updates checksums atomically, resets
runtime adoption to `pending-review`, and exits:

```bash
python3 hack/llm-upstream/sync.py update \
  --lane glm53 \
  --revision <full-reviewed-commit-sha>
python3 hack/llm-upstream/sync.py drift --lane glm53
python3 hack/llm-upstream/sync.py check --lane glm53
```

For a pre-fetched checkout or a test fixture, make the export itself offline:

```bash
python3 hack/llm-upstream/sync.py update \
  --lane glm53 --revision <full-sha> --source /path/to/upstream-checkout
```

When reviewed HEAD is documentation-only, preserve the older runtime snapshot
while recording the newer review boundary. DSV41 currently uses this form:

```bash
python3 hack/llm-upstream/sync.py update \
  --lane dsv41 \
  --revision e2944b34ebfd78f02b469423ea0490749515a396 \
  --reviewed-revision 979e68a62c90b24d928f5638596e0ceed90e9f34
```

Always inspect the resulting lock, `vendor/SOURCE.json`, `drift.md`, and manifest
semantic diff. An updater success is not approval to deploy. GLM runtime
adoption remains blocked until an immutable image is proven to contain the
reviewed recipe and the stale local ConfigMap overlays are reconciled together.
