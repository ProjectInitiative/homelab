#!/bin/bash
set -euo pipefail

echo "=== Step 0: Generate SSL certs ==="
bash generate-certs.sh

echo ""
echo "=== Step 1: Create rclone config (you must edit this first!) ==="
echo "Edit 01-rclone-config-secret.yaml with your actual rclone.conf, then run:"
echo ""
echo "  kubectl apply -f 01-rclone-config-secret.yaml"
echo "  kubectl apply -f 02-ftps-ssl-certs.yaml"
echo "  kubectl apply -f 04-deployment.yaml"
echo "  kubectl apply -f 05-service.yaml"
echo ""

echo "After deploying, update the pasv_address in the deployment:"
echo "  1. kubectl -n default get svc gdrive-ftps -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"
echo "  2. kubectl -n default set env deploy/ftps-gdrive VSFTPD_PASV_ADDRESS=<hostname>"
echo ""
echo "Or edit the deployment and update the env var, then: kubectl rollout restart deploy/ftps-gdrive"
