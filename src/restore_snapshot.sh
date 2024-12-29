#!/usr/bin/env bash

set -e

if [[ -z "${GITHUB_TOKEN}" ]]
then
    echo "GITHUB_TOKEN is not set"
    exit 0
else
    echo "GITHUB_TOKEN is set to ${GITHUB_TOKEN}"

    echo "runpod-worker-comfy: restoring snapshot"
    python3 download_assets.py --version $VERSION --github_token $GITHUB_TOKEN
    echo "runpod-worker-comfy: restored snapshot successfully"
fi


if [[ -z "${HUGGINGFACE_ACCESS_TOKEN}" ]]
then
    echo "HUGGINGFACE_ACCESS_TOKEN is not set"
    exit 0
else
    huggingface-cli login --token ${HUGGINGFACE_ACCESS_TOKEN}
    echo "HUGGINGFACE_ACCESS_TOKEN is set and logged in successfully"
fi