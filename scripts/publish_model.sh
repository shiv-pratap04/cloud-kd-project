#!/usr/bin/env bash
# Usage: scripts/publish_model.sh v1 build/model_v1
# Uploads model to the bucket (models/<v>/), writes model.sha256 = SHA-256 of the release tarball,
# and attaches that same tarball to a GitHub Release (requires `gh auth login`).
set -euo pipefail
V=$1; DIR=$2
TAR="build/model_${V}.tar.gz"
tar --sort=name --mtime='2000-01-01' --owner=0 --group=0 -C "$DIR" -czf "$TAR" .
sha256sum "$TAR" | awk '{print $1"  model_'"$V"'.tar.gz"}' > "$DIR/model.sha256"
cp "$DIR/model.sha256" "build/model_${V}.sha256"
scripts/with_s3.sh python scripts/s3tool.py putdir models "$V" "$DIR"
mkdir -p results && cp "$DIR/model.sha256" "results/model_${V}.sha256"
gh release view "$V" >/dev/null 2>&1 || gh release create "$V" --title "model $V" --notes "Distilled Pythia-70M ($V)"
gh release upload "$V" "$TAR" "build/model_${V}.sha256" --clobber
cat "$DIR/model.sha256"
