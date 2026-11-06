GH_REPO ?= shiv-pratap04/cloud-kd-project
SUBSET  ?= 0
export GH_REPO

.PHONY: up down train lint test teacher clean-data deploy images
# Fresh clone:  make up   (needs docker, k3d, kubectl, curl, python3 with boto3)
up:
	k3d cluster create --config cluster/k3d.yaml || true
	scripts/secrets.sh
	kubectl apply -f k8s/10-seaweedfs.yaml
	kubectl -n data rollout status deploy/seaweedfs --timeout=180s
	scripts/with_s3.sh python scripts/s3tool.py mkbuckets
	scripts/with_s3.sh python scripts/s3tool.py put datasets commands_pool.jsonl data/commands_pool.jsonl
	scripts/seed_models.sh
	$(MAKE) deploy

images:
	docker build -f service/Dockerfile -t parser-service:1 .
	docker build -f worker/Dockerfile -t teacher-worker:1 .
	k3d image import parser-service:1 teacher-worker:1 -c cloudlab

deploy: images
	kubectl apply -f k8s/30-app.yaml
	kubectl -n app rollout status deploy/parser --timeout=300s

teacher:   ## Task 1 (Ollama must be running on the host with phi3.5 pulled)
	kubectl apply -f k8s/20-teacher-job.yaml
	kubectl -n pipeline wait --for=condition=complete job/teacher-labelling --timeout=24h

clean-data: ## runs worker/clean.py against the shards in object storage
	scripts/with_s3.sh sh -c 'S3_ENDPOINT=http://localhost:8333 AWS_ACCESS_KEY_ID=$$(grep S3_ACCESS_KEY .env|cut -d= -f2) AWS_SECRET_ACCESS_KEY=$$(grep S3_SECRET_KEY .env|cut -d= -f2) python worker/clean.py'

train:
	python training/train.py --config training/config.yaml $(if $(filter-out 0,$(SUBSET)),--subset $(SUBSET),)

lint:
	ruff check .

test:
	python -m pytest -q tests

down:
	k3d cluster delete cloudlab
