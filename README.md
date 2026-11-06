# Cloud Computing mini project: distilled command parser (Pythia-70M) on k3d

Name: Shiv Pratap Singh    Roll number: 230101097
GitHub repo: https://github.com/shiv-pratap04/cloud-kd-project

## Prerequisites
Docker, k3d, kubectl, curl, gh (for releases), Python 3.12 with `pip install -r requirements-dev.txt`
(`boto3` is required by `make up`). Ollama with `phi3.5` pulled, only for Task 1 labelling.

## Build and deploy (fresh clone)
    make up        # k3d cluster, SeaweedFS, secrets, buckets, models from the GitHub Releases, image build, app deploy
    curl -si -X POST localhost:8080/parse -H 'Content-Type: application/json' -d '{"text":"what is the weather in london"}'

## Tear down
    make down

## Reproduce the pipeline
    make images && make teacher        # Task 1 labelling (Ollama on the host, WSL gateway address in k8s/20-teacher-job.yaml)
    make clean-data                    # Task 1 cleaning + checksum
    make train SUBSET=50               # smoke test
    make train                         # trains v1 (config in training/config.yaml)
    scripts/publish_model.sh v1 build/model_v1

## Evaluate, test, load
    python scripts/predict.py hf build/model_v1 results/student_predictions.jsonl
    python tools/score.py results/student_predictions.jsonl data/validation.jsonl
    make test ; make lint
    scripts/loadtest.sh loadtest        # standard Locust run through the Ingress
    python scripts/cost.py 2 1 1 4.587

Evidence for every task is in `results/`; the report is `report/report.pdf`.
