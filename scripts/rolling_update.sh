#!/usr/bin/env bash
cd "$(dirname "$0")/.."; mkdir -p results
OUT=results/rolling_events.txt; : > $OUT
note() { echo "$(date +%H:%M:%S) $*" | tee -a $OUT; }
check() { for i in 1 2 3 4 5 6; do curl -si -X POST localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"what is the weather in london"}' | grep -iE "^x-model-version|^x-served-by" | tr '\r\n' '  '; echo; done | tee -a $OUT; }
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 7m --host http://localhost:8080 --csv results/rolling > results/rolling_locust.log 2>&1 &
LP=$!
sleep 45
note "version headers before update:"; check
note "SET MODEL_VERSION=v2 MODEL_URI=s3://models/v2/"
kubectl -n app set env deploy/parser MODEL_VERSION=v2 MODEL_URI=s3://models/v2/ 2>&1 | tee -a $OUT
kubectl -n app rollout status deploy/parser --timeout=400s 2>&1 | tee -a $OUT
note "rollout to v2 complete"; sleep 20
note "version headers after update:"; check
note "ROLLBACK: kubectl rollout undo"
kubectl -n app rollout undo deploy/parser 2>&1 | tee -a $OUT
kubectl -n app rollout status deploy/parser --timeout=400s 2>&1 | tee -a $OUT
note "rollback complete"; sleep 20
note "version headers after rollback:"; check
kubectl -n app get pods | tee -a $OUT
note "waiting for load test to finish"
wait $LP
note "done"
