# ---------------------------------------------------------------------------- #
#                         Stage 1: Download the Base                           #
# ---------------------------------------------------------------------------- #
ARG BASE_IMAGE="nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04" 

FROM ${BASE_IMAGE}

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV SHELL=/bin/bash
ENV PYTHONUNBUFFERED=True
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_PREFER_BINARY=True
# Faster transfer of models from the hub to the container
ENV HF_HUB_ENABLE_HF_TRANSFER="1"
ENV NVIDIA_VISIBLE_DEVICES=all

# ---------------------------------------------------------------------------- #
#                         Stage 2: Mount Volume, Add & Update                  #
# ---------------------------------------------------------------------------- #

ENV MODELS="/runpod-volume/models/"
ENV CUSTOM_NODES="/runpod-volume/custom_nodes/"

# Install Python, git and other necessary tools
# Upgrade apt packages and install required dependencies
RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      python3-dev \
      python3-pip \
      fonts-dejavu-core \
      rsync \
      git \
      jq \
      moreutils \
      aria2 \
      wget \
      curl \
      libglib2.0-0 \
      libsm6 \
      libgl1 \
      libxrender1 \
      libxext6 \
      ffmpeg \
      bc \
      libgoogle-perftools4 \
      libtcmalloc-minimal4 \
      procps

# Clean up to reduce image size
RUN apt-get autoremove -y && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set Python
RUN ln -sf /usr/bin/python3.10 /usr/bin/python

# Install pip drop-in replacement uv (https://github.com/astral-sh/uv)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh


# ---------------------------------------------------------------------------- #
#                         Stage 3: ComfyUI & Add Pip Modules                   #
# ---------------------------------------------------------------------------- #

# Clone ComfyUI repository
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /comfyui

# Change working directory to ComfyUI
WORKDIR /comfyui

# Install ComfyUI dependencies
RUN pip3 install --upgrade --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 \
    && pip3 install --upgrade -r requirements.txt

# Install necessary Python packages
COPY requirements.txt /requirements.txt
RUN pip install --upgrade --no-cache-dir pip && \
    pip install --upgrade --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt

# Install Worker dependencies
RUN pip install requests runpod huggingface_hub

# ---------------------------------------------------------------------------- #
#                         Stage 4: Soft Links                                  #
# ---------------------------------------------------------------------------- #

# Support for the network volume
ADD src/extra_model_paths.yaml ./

# Go back to the root
WORKDIR /

# Add the start and the handler
ADD src/start.sh src/rp_handler.py test_input.json ./

# Copy all folder and overwrite if exists
COPY src/ ./src/
COPY $MODELS /comfyui/models
COPY $CUSTOM_NODES /comfyui/custom_nodes

# Run start 
RUN chmod +x /start.sh 

# Start the container
ENTRYPOINT [ "/start.sh" ]