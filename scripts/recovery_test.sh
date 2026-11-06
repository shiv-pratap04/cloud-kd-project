#!/usr/bin/env bash
cd "$(dirname "$0")/.."; mkdir -p results
OUT=results/recovery_events.txt; : > $OUT
note() { echo "$(date +%H:%M:%S) $*" | tee -a $OUT; }
ready() { kubectl -n app get pods -o json | python3 -c "
import json,sys
n=0
for p in json.load(sys.stdin)['items']:
    if p['metadata'].get('deletionTimestamp'): continue
    if any(c['type']=='Ready' and c['status']=='True' for c in p['status'].get('conditions',[])): n+=1
print(n)"; }
kubectl -n app scale deploy parser --replicas=2 >/dev/null
kubectl -n app rollout status deploy/parser --timeout=300s >/dev/null
note "start: $(ready) ready pods"
locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 3m --host http://localhost:8080 --csv results/recovery > results/recovery_locust.log 2>&1 &
LP=$!
sleep 45
VICTIM=$(kubectl -n app get pods -o name | head -1)
note "DELETE $VICTIM"
T0=$(date +%s)
kubectl -n app delete $VICTIM --wait=false | tee -a $OUT
for i in $(seq 120); do
  R=$(ready); note "ready (non-terminating) pods: $R"
  if [ "$i" -gt 2 ] && [ "$R" = 2 ]; then note "RESTORED to 2 ready pods after $(( $(date +%s) - T0 )) s"; break; fi
  sleep 1
done
kubectl -n app get pods | tee -a $OUT
wait $LP; note done
