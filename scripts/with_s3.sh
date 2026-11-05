#!/usr/bin/env bash
# Run a command with a temporary port-forward to SeaweedFS: scripts/with_s3.sh python scripts/s3tool.py ...
kubectl -n data port-forward svc/seaweedfs 8333:8333 >/dev/null 2>&1 &
PF=$!; trap 'kill $PF 2>/dev/null' EXIT
for i in $(seq 30); do (echo > /dev/tcp/127.0.0.1/8333) 2>/dev/null && break; sleep 1; done
"$@"
