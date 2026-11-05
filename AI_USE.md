# AI use

**Tools:** Claude (Anthropic), used for scaffolding repository code, manifests and CI, and for explaining Kubernetes/NACL concepts.

**What it produced:** first drafts of worker/, service/, training/, k8s/, Makefile, CI workflow, network/nacl.json and subnets.md.

**How I checked it:** (edit this to reflect what you actually did)
- Ran nacl_sim.py on the sample packets and extra packets I wrote myself; recomputed subnets by hand.
- Unit tests for cleaning/validation/sharding; ran clean.py on real shards and checked that the counts add up.
- Read every manifest and script line by line; ran each stage on my machine and kept the command output in results/.
- Did NOT trust any result I did not produce myself: all scores, latencies and costs in the report come from my own runs.
