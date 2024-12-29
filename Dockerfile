#
# Stage 1: Base image with common dependencies
#
ARG CUDA_VERSION="12.1.1"
ARG CUDNN_VERSION="8"
ARG UBUNTU_VERSION="22.04"
ARG DOCKER_FROM=nvidia/cuda:$CUDA_VERSION-cudnn$CUDNN_VERSION-devel-ubuntu$UBUNTU_VERSION   

# Base NVidia CUDA Ubuntu image
FROM $DOCKER_FROM AS base

# Prevents prompts from packages asking for user input during installation
ENV DEBIAN_FRONTEND=noninteractive
# Prefer binary wheels over source distributions for faster pip installations
ENV PIP_PREFER_BINARY=1
# Ensures output from python is printed immediately to the terminal without buffering
ENV PYTHONUNBUFFERED=1 
# Speed up some cmake builds
ENV CMAKE_BUILD_PARALLEL_LEVEL=8

# Install Python, git and other necessary tools
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    wget \
    libgl1 \
    && ln -sf /usr/bin/python3.10 /usr/bin/python \
    && ln -sf /usr/bin/pip3 /usr/bin/pip

# Clean up to reduce image size
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

#
#  Stage 2: Install ComfyUI and RunPod
#

# Install comfy-cli
RUN pip install comfy-cli

# Install ComfyUI
RUN /usr/bin/yes | comfy --workspace /comfyui install --cuda-version 12.1 --nvidia --version 0.3.10

# Change working directory to ComfyUI
WORKDIR /comfyui

#
#   Stage 3: Install RunPod and dependencies
#

# Install runpod
RUN pip install runpod requests

# Support for the network volume
ADD src/extra_model_paths.yaml ./

#
#   Stage 4: Add scripts and copy files


# Go back to the root
WORKDIR /

# Add scripts
ADD src/start.sh src/restore_snapshot.sh src/rp_handler.py ./
RUN chmod +x /start.sh /restore_snapshot.sh

# Copy the workflows to the root folder
RUN mkdir -p /workflows
ADD workflows/* /workflows/

# Accept build arguments
ARG GITHUB_TOKEN
ARG VERSION
ARG HUGGINGFACE_ACCESS_TOKEN
ARG SERVE_API_LOCALLY

# Set environment variables
ENV GITHUB_TOKEN=${GITHUB_TOKEN}
ENV VERSION=${VERSION}
ENV HUGGINGFACE_ACCESS_TOKEN=${HUGGINGFACE_ACCESS_TOKEN}
ENV SERVE_API_LOCALLY=${SERVE_API_LOCALLY}

# Echo environment variables    
RUN echo "SERVE_API_LOCALLY=${SERVE_API_LOCALLY}" && echo "GITHUB_TOKEN=${GITHUB_TOKEN}" && echo "VERSION=${VERSION}"

# Change working directory to ComfyUI
WORKDIR /comfyui

# Files to download nodes
ADD restore-snapshot/* /comfyui/
# Install all nodes
RUN /restore_snapshot.sh

# Link volume models to local folder
RUN rm -rf models && ln -s /workspace/models ./

# Network port for RunPod API
EXPOSE 8188

# Set te default command to execute when container starts
CMD ["/start.sh"]