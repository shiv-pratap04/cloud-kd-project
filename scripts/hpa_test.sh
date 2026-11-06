#!/usr/bin/env bash
cd "$(dirname "$0")/.."; mkdir -p results
OUT=results/hpa_timeline.txt; : > $OUT
log() { echo "$(date +%H:%M:%S) $1 | $(kubectl -n app get hpa parser --no-headers | tr -s ' ')" >> $OUT; }
reps() { kubectl -n app get deploy parser -o jsonpath='{.status.replicas}'; }
echo "phase 1: idle, waiting for scale-down to 1"
for i in $(seq 50); do log idle; [ "$(reps)" = 1 ] && break; sleep 15; done
echo "phase 2: load"
( while true; do log load; sleep 15; done ) & LP=$!
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 3m --host http://localhost:8080 --csv results/hpa_load > results/hpa_locust.log 2>&1
kill $LP
echo "phase 3: idle again, waiting for scale-down to 1"
for i in $(seq 50); do log idle2; [ "$(reps)" = 1 ] && break; sleep 15; done
log done; cat $OUT
