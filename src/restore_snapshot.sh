#!/usr/bin/env bash

set -e

if [ -z "$GITHUB_TOKEN" ]; then
    echo "runpod-worker-comfy: No GITHUB_TOKEN found. "
    exit 0
fi

echo "runpod-worker-comfy: restoring snapshot"

python3 /comfyui/download_assets.py --version $VERSION --github_token $GITHUB_TOKEN

echo "runpod-worker-comfy: restored snapshot successfully"