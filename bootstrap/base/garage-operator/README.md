# garage-operator staged deployment
#
# The rajsinghtech garage-operator helm chart is an OCI chart. Our CMP
# (kustomized-git-helm) renders git-hosted charts via git-chart.yaml; for OCI
# charts the simplest GitOps-shaped path is a pinned helm template committed
# here OR a one-time `helm template | kustomize` refresh.
#
# To keep this base valid kustomize input BEFORE enablement (so nothing breaks
# the app catalog validation), this directory currently contains:
#   - kustomization.yaml        (documentation + future helm wiring)
#   - management-handle.yaml    (management-handle GarageCluster, needs operator)
#   - bucket-and-key.yaml       (GarageBucket + GarageKey for esu-sound-library)
#   - docs note: ../../docs/garage-operator-staging.md
#
# The operator itself (Deployment + CRDs) is intentionally NOT rendered here yet:
# it must be enabled deliberately (staging doc §3) to avoid a half-installed
# webhook-blocking state.
