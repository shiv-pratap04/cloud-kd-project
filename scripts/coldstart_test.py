import json, subprocess, time, statistics
from datetime import datetime
def sh(*a): return subprocess.run(a, capture_output=True, text=True).stdout
def ts(s): return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
subprocess.run(["kubectl", "-n", "app", "scale", "deploy/parser", "--replicas=2"])
runs, out = [], open("results/coldstart.txt", "w")
def log(m): print(m); out.write(m + "\n"); out.flush()
for run in (1, 2, 3):
    old = {p["metadata"]["name"] for p in json.loads(sh("kubectl", "-n", "app", "get", "pods", "-o", "json"))["items"]}
    sh("kubectl", "-n", "app", "delete", "pods", "--all", "--wait=false")
    log(f"run {run}: deleted all pods at {time.strftime('%H:%M:%S')}")
    for _ in range(120):
        time.sleep(3)
        new = [p for p in json.loads(sh("kubectl", "-n", "app", "get", "pods", "-o", "json"))["items"]
               if p["metadata"]["name"] not in old and not p["metadata"].get("deletionTimestamp")]
        ready = []
        for p in new:
            c = [c for c in p["status"].get("conditions", []) if c["type"] == "Ready" and c["status"] == "True"]
            if c: ready.append((p["metadata"]["name"], (ts(c[0]["lastTransitionTime"]) - ts(p["metadata"]["creationTimestamp"])).total_seconds()))
        if len(ready) >= 2: break
    for n, t in ready: log(f"  {n}: creation->Ready {t:.0f} s")
    runs.append(max(t for _, t in ready))
    log(f"  run {run} cold-start (slowest pod): {runs[-1]:.0f} s")
    for n, _ in ready: log("  log: " + " | ".join(sh("kubectl", "-n", "app", "logs", n).split("\n")[-8:-1] if False else [l for l in sh("kubectl", "-n", "app", "logs", n).split("\n") if "downloaded" in l or "model ready" in l]))
log(f"runs: {[round(r) for r in runs]} s, MEDIAN {statistics.median(runs):.0f} s")
