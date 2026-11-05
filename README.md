# Cloud Computing mini project: distilled command parser (Pythia-70M) on k3d

GitHub repo: <PASTE YOUR REPO LINK HERE>      Name / roll number: <FILL IN>

## Prerequisites
docker, k3d, kubectl, python 3.11, `pip install -r requirements-dev.txt`, Ollama with `ollama pull phi3.5`, `gh` (for releases).
Set `GH_REPO=<user>/<repo>` (Makefile variable) before `make up`.

## Run order (what you do once, in this order)
1. `make up` (cluster + SeaweedFS + secrets + buckets + models + app). Before the models exist, run only the first steps; seed_models needs the Releases from step 5.
2. Start Ollama on the host: `OLLAMA_HOST=0.0.0.0 ollama serve`, then `make images && make teacher`  (Task 1, several hours).
3. `make clean-data`, record the counts and checksum; copy the result: `scripts/with_s3.sh python scripts/s3tool.py get datasets v1/train.jsonl data/train.jsonl` (plus train.sha256).
4. `make train SUBSET=50` (smoke test), then `make train` (v1); for v2: `python training/train.py --out build/model_v2 --epochs 4 --seed 7`.
5. `scripts/publish_model.sh v1 build/model_v1` and `... v2 build/model_v2`.
6. Evaluate three models into results/ (see below), then `make deploy`.
7. Task 4 experiments, Task 7 load tests, write the report, `git tag final`.

## Evaluation commands
    python scripts/predict.py teacher http://localhost:11434 results/teacher_predictions.jsonl
    python tools/score.py results/teacher_predictions.jsonl data/validation.jsonl --out results/teacher_validation.json
    python scripts/predict.py hf EleutherAI/pythia-70m results/base_predictions.jsonl
    python scripts/predict.py hf build/model_v1 results/student_predictions.jsonl
    (score each with tools/score.py --out results/<name>.json)

## Test / load
    make test ; make lint
    locust -f tools/locustfile.py --headless --users 4 --spawn-rate 4 --run-time 2m --host http://localhost:8080 --csv results/loadtest
    python scripts/cost.py REPLICAS CPU_LIMIT MEM_GIB REQUESTS_PER_SEC

## Task 3 container check
    docker run --rm --cpus=1 --memory=1g -p 8000:8000 -e MODEL_URI=... -e S3_ENDPOINT=... -e AWS_ACCESS_KEY_ID=... -e AWS_SECRET_ACCESS_KEY=... parser-service:1
    docker stats --no-stream   # record peak memory while sending 50 requests

## Tear down
    make down
