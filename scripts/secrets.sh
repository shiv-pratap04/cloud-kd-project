#!/usr/bin/env bash
# Generates random S3 keys into .env (gitignored) and creates the Kubernetes Secrets.
set -euo pipefail
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  { echo "S3_ACCESS_KEY=$(head -c 12 /dev/urandom | base64 | tr -dc A-Za-z0-9)";
    echo "S3_SECRET_KEY=$(head -c 24 /dev/urandom | base64 | tr -dc A-Za-z0-9)"; } > .env
fi
source .env
kubectl apply -f k8s/00-namespaces.yaml
cat > /tmp/s3.json <<JSON
{"identities":[{"name":"admin","credentials":[{"accessKey":"$S3_ACCESS_KEY","secretKey":"$S3_SECRET_KEY"}],"actions":["Admin","Read","Write","List","Tagging"]}]}
JSON
kubectl -n data create secret generic seaweed-s3-config --from-file=s3.json=/tmp/s3.json --dry-run=client -o yaml | kubectl apply -f -
rm -f /tmp/s3.json
for ns in pipeline app; do
  kubectl -n $ns create secret generic s3-credentials \
    --from-literal=AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY" --from-literal=AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY" \
    --dry-run=client -o yaml | kubectl apply -f -
done
