#!/usr/bin/env bash
# From a fresh clone: fetch released models and put them in object storage (models/v1, models/v2).
set -euo pipefail
: "${GH_REPO:?set GH_REPO=<user>/<repo>}"
mkdir -p build
for V in v1 v2; do
  curl -fsSL -o "build/model_${V}.tar.gz" "https://github.com/${GH_REPO}/releases/download/${V}/model_${V}.tar.gz"
  curl -fsSL -o "build/model_${V}.sha256" "https://github.com/${GH_REPO}/releases/download/${V}/model_${V}.sha256"
  (cd build && echo "$(cut -d' ' -f1 model_${V}.sha256)  model_${V}.tar.gz" | sha256sum -c -)
  rm -rf "build/seed_${V}" && mkdir -p "build/seed_${V}" && tar -xzf "build/model_${V}.tar.gz" -C "build/seed_${V}"
  cp "build/model_${V}.sha256" "build/seed_${V}/model.sha256"
done
for V in v1 v2; do scripts/with_s3.sh python scripts/s3tool.py putdir models "$V" "build/seed_${V}"; done
