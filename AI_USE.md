# AI use

**Tool:** Claude (Anthropic), in a chat interface.

**What I used it for:**
- Drafting the first version of the repository: worker, `clean.py`, training script, FastAPI service, Dockerfiles, Kubernetes manifests, Makefile, CI workflow, NACL file and subnet table.
- Explaining errors I pasted in (Ollama reachability from WSL and from the cluster, git repository mistakes, CI Python version, rollout timeouts).
- Suggesting experiment scripts for the HPA, rolling update, recovery and cold-start tests.

**How I checked what it gave me:**
- Ran everything myself on my laptop and kept the command output in `results/`. All scores, latencies and costs in the report come from these runs.
- Checked the teacher on sample commands first; the first test showed a reply that rambled past the JSON, so I added a stop sequence (a generation setting, the prompt is unchanged).
- Re-computed subnets by hand and checked the NACL with `nacl_sim.py` on the sample packets.
- Verified shard coverage with a script (3,000 ids, no gaps, no repeats), and reproduced the `train.jsonl` checksum.
- Caught problems in the AI's work: the first rolling update had 0.72% failures (over the 0.5% target), which led to the graceful-shutdown change; the first recovery test reported a 0 s recovery from a stale status field, so it was redone.
- I did not accept any result I could not reproduce.
