#!/usr/bin/env bash

echo "Worker Initiated"

# Use libtcmalloc for better memory management
TCMALLOC="$(ldconfig -p | grep -Po "libtcmalloc.so.\d" | head -n 1)"
export LD_PRELOAD="${TCMALLOC}"

# To test if in Dockerfile not works
echo "Symlinking files from Network Volume"
ln -s /runpod-volume /workspace
# cancello le cartelle di default 
rm -rf /comfyui/models \ 
rm -rf /comfui/custom_nodes 
# creo soft link nelle cartelle 
ln -s /workspace/models /comfyui/models
ln -s /workspace/custom_nodes /comfyui/custom_nodes

# by default the network volume is mounted to /runpod-volume in serverless, while /workspace in regular pods
# export RUNPOD_NETWORK_VOLUME_PATH="/workspace"

# Check or Download Weights
python3 /check_or_download.py


# Serve the API and don't shutdown the container
if [ "$SERVE_API_LOCALLY" == "true" ]; then
    echo "runpod-worker-comfy: Starting ComfyUI"
    python3 /comfyui/main.py --disable-auto-launch --disable-metadata --listen &

    echo "runpod-worker-comfy: Starting RunPod Handler"
    python3 -u /rp_handler.py --rp_serve_api --rp_api_host=0.0.0.0
else
    echo "runpod-worker-comfy: Starting ComfyUI"
    python3 /comfyui/main.py --disable-auto-launch --disable-metadata &

    echo "runpod-worker-comfy: Starting RunPod Handler"
    python3 -u /rp_handler.py
fi