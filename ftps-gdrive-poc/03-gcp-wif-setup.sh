#!/bin/bash
set -euo pipefail

# ─────────────────────────────────────────────────────────────
# GCP Workload Identity Federation Setup
# Run this once to bridge trust between your cluster and GCP.
# ─────────────────────────────────────────────────────────────

PROJECT_ID="${1:?Usage: $0 <gcp-project-id> [gcp-sa-email]}"
SA_EMAIL="${2:-rclone-gdrive@${PROJECT_ID}.iam.gserviceaccount.com}"
POOL_NAME="local-k8s-pool"
PROVIDER_NAME="local-k8s-provider"

echo "=== Step 1: Export cluster JWKS ==="
kubectl get --raw /openid/v1/jwks > cluster-jwks.json

ISSUER_URL=$(kubectl get --raw /.well-known/openid-configuration | jq -r .issuer)
echo "Issuer URL: $ISSUER_URL"

echo ""
echo "=== Step 2: Create Workload Identity Pool ==="
gcloud iam workload-identity-pools create "$POOL_NAME" \
    --location="global" \
    --project="$PROJECT_ID" \
    --display-name="Local K8s Pool" \
    2>/dev/null || echo "Pool already exists, skipping..."

echo ""
echo "=== Step 3: Create OIDC Provider (uploads cluster JWKS) ==="
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_NAME" \
    --location="global" \
    --project="$PROJECT_ID" \
    --workload-identity-pool="$POOL_NAME" \
    --issuer-uri="$ISSUER_URL" \
    --jwks-json="$(cat cluster-jwks.json)" \
    --attribute-mapping="google.subject=assertion.sub" \
    2>/dev/null || echo "Provider already exists, skipping..."

echo ""
echo "=== Step 4: Grant SA impersonation to the K8s SA ==="
gcloud iam service-accounts add-iam-policy-binding "$SA_EMAIL" \
    --project="$PROJECT_ID" \
    --role="roles/iam.workloadIdentityUser" \
    --member="principal://iam.googleapis.com/projects/$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')/locations/global/workloadIdentityPools/$POOL_NAME/subject/system:serviceaccount:default:ftps-gdrive"

echo ""
echo "=== Step 5: Generate credential config ==="
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

gcloud iam workload-identity-pools create-cred-config \
    "projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL_NAME/providers/$PROVIDER_NAME" \
    --service-account="$SA_EMAIL" \
    --output-file=sts-creds.json \
    --credential-source-file=/var/run/secrets/kubernetes.io/serviceaccount/token

echo ""
echo "=== Step 6: Create ConfigMap from credential config ==="
kubectl create configmap gcp-auth-config \
    --namespace default \
    --from-file=sts-creds.json \
    --dry-run=client -o yaml > 03-gcp-auth-config.yaml

echo ""
echo "Done! Generated:"
echo "  cluster-jwks.json   (safe to discard after setup)"
echo "  03-gcp-auth-config.yaml  (ConfigMap with sts-creds.json)"
echo ""
echo "Now run:  kubectl apply -f 03-gcp-auth-config.yaml"
