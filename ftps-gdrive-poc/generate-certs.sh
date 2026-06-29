#!/bin/bash
set -euo pipefail

CERT_DIR=$(mktemp -d)
trap 'rm -rf "$CERT_DIR"' EXIT

openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout "$CERT_DIR/vsftpd.key" \
  -out "$CERT_DIR/vsftpd.crt" \
  -subj "/CN=gdrive-ftps/O=Homelab POC"

cat "$CERT_DIR/vsftpd.crt" "$CERT_DIR/vsftpd.key" > "$CERT_DIR/vsftpd.pem"

kubectl create secret generic ftps-ssl-certs \
  --namespace default \
  --from-file=vsftpd.pem="$CERT_DIR/vsftpd.pem" \
  --from-file=vsftpd.crt="$CERT_DIR/vsftpd.crt" \
  --from-file=vsftpd.key="$CERT_DIR/vsftpd.key" \
  --dry-run=client -o yaml > 02-ftps-ssl-certs.yaml

echo "Generated 02-ftps-ssl-certs.yaml"
