#!/bin/bash
set -euo pipefail

echo "=== Step 0: Generate SSL certs ==="
bash generate-certs.sh

echo ""
echo "Edit 01-rclone-config-secret.yaml with your actual rclone.conf, then run:"
echo ""
echo "  kubectl apply -f 01-rclone-config-secret.yaml"
echo "  kubectl apply -f 02-ftps-ssl-certs.yaml"
echo "  kubectl apply -f 03-deployment.yaml"
echo "  kubectl apply -f 05-service.yaml"
