#!/usr/bin/env bash
# Task 3: run the service image at 1 CPU / 1 GiB, send 50 sequential requests, report peak memory.
set -uo pipefail
cd "$(dirname "$0")/.."
source .env
IP=$(hostname -I | awk '{print $1}')
mkdir -p build
kubectl -n data port-forward --address 0.0.0.0 svc/seaweedfs 8333:8333 >/dev/null 2>&1 &
PF=$!
trap 'kill $PF $MON 2>/dev/null; docker rm -f parser-test >/dev/null 2>&1' EXIT
sleep 3
docker rm -f parser-test >/dev/null 2>&1
code=$(docker run --rm curlimages/curl -s -o /dev/null -w '%{http_code}' --max-time 8 http://$IP:8333/ || true)
echo "container -> SeaweedFS check: HTTP $code"
[ "$code" = "000" ] && { echo "container cannot reach $IP:8333"; exit 1; }
docker run -d --name parser-test --cpus=1 --memory=1g -p 8000:8000 \
  -e MODEL_URI=s3://models/v1/ -e MODEL_VERSION=v1 -e S3_ENDPOINT=http://$IP:8333 -e MAX_NEW_TOKENS=80 \
  -e AWS_ACCESS_KEY_ID=$S3_ACCESS_KEY -e AWS_SECRET_ACCESS_KEY=$S3_SECRET_KEY parser-service:1 >/dev/null
( while true; do docker stats --no-stream --format '{{.MemUsage}}' parser-test; sleep 1; done > build/mem_samples.txt ) &
MON=$!
for i in $(seq 150); do
  [ "$(curl -s -o /dev/null -w '%{http_code}' localhost:8000/readyz)" = 200 ] && { echo "ready after ~$((i*2))s"; break; }
  sleep 2
done
python3 - <<'PY'
import json, time, urllib.request
cmds = [json.loads(l)["text"] for l in open("data/validation.jsonl")][:50]
ok, lat = 0, []
for c in cmds:
    t = time.time()
    req = urllib.request.Request("http://localhost:8000/parse", json.dumps({"text": c}).encode(), {"Content-Type": "application/json"})
    try:
        r = urllib.request.urlopen(req, timeout=60); ok += r.status == 200
    except Exception as e:
        print("request failed:", e)
    lat.append(time.time() - t)
lat.sort()
print(f"requests: 50, HTTP 200: {ok}, median {lat[25]:.2f}s, max {lat[-1]:.2f}s")
PY
sleep 2; kill $MON 2>/dev/null
python3 - <<'PY'
import re
u = {"KiB": 1/1024, "MiB": 1, "GiB": 1024}
v = [float(m.group(1)) * u[m.group(2)] for l in open("build/mem_samples.txt") if (m := re.match(r"([\d.]+)(KiB|MiB|GiB)", l))]
print(f"peak memory: {max(v):.0f} MiB (limit 1024 MiB, {len(v)} samples)")
PY
echo "OOMKilled: $(docker inspect parser-test --format '{{.State.OOMKilled}}')  RestartCount: $(docker inspect parser-test --format '{{.RestartCount}}')"
