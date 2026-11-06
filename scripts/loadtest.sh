#!/usr/bin/env bash
# Standard load test (4 users, 2 min) through the Ingress, plus cluster snapshots.
TAG=${1:-loadtest}; cd "$(dirname "$0")/.."; mkdir -p results
{ echo "== before"; kubectl -n app get pods,hpa; } > results/${TAG}_cluster.txt 2>&1
( sleep 60; { echo "== kubectl top pods at 60s"; kubectl -n app top pods; echo "== hpa at 60s"; kubectl -n app get hpa; } >> results/${TAG}_cluster.txt 2>&1 ) &
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/$TAG 2>&1 | tee results/${TAG}_locust.log
wait
{ echo "== after"; kubectl -n app get pods,hpa; } >> results/${TAG}_cluster.txt 2>&1
