#!/usr/bin/env bash
cd "$(dirname "$0")/.."; mkdir -p results
OUT=results/recovery_events.txt; : > $OUT
note() { echo "$(date +%H:%M:%S) $*" | tee -a $OUT; }
kubectl -n app scale deploy parser --replicas=2 >/dev/null
kubectl -n app rollout status deploy/parser --timeout=300s >/dev/null
note "start: $(kubectl -n app get deploy parser -o jsonpath='{.status.readyReplicas}') ready"
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 3m --host http://localhost:8080 --csv results/recovery > results/recovery_locust.log 2>&1 &
LP=$!
sleep 45
VICTIM=$(kubectl -n app get pods -o name | head -1)
note "DELETE $VICTIM"
kubectl -n app delete $VICTIM --wait=false | tee -a $OUT
T0=$(date +%s)
for i in $(seq 40); do
  R=$(kubectl -n app get deploy parser -o jsonpath='{.status.readyReplicas}'); R=${R:-0}
  note "ready replicas: $R"
  [ "$R" = 2 ] && { note "RESTORED after $(( $(date +%s) - T0 )) s"; break; }
  sleep 3
done
kubectl -n app get pods | tee -a $OUT
wait $LP; note done
