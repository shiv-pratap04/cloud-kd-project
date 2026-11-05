"""Task 7 cost: python scripts/cost.py REPLICAS CPU_LIMIT MEM_GIB REQUESTS_PER_SEC"""
import json, sys
rc = json.load(open("data/rate_card.json"))
n, cpu, mem, rps = int(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
hourly = n * (cpu * rc["vcpu_hour"] + mem * rc["gib_memory_hour"])
per_hour = rps * 3600
print(f"hourly cost = {n} x ({cpu} x {rc['vcpu_hour']} + {mem} x {rc['gib_memory_hour']}) = {hourly:.4f} {rc['currency']}")
print(f"requests/hour = {rps} x 3600 = {per_hour:.0f}")
print(f"cost per 1000 requests = {hourly}/{per_hour:.0f} x 1000 = {hourly / per_hour * 1000:.4f} {rc['currency']}")
