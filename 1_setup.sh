#!/usr/bin/env bash

VENV_FOLDER="venv"
DIRECTORY="./data"

# Create environment 
if ! [ -d "$VENV_FOLDER" ]; then
    python3 -m venv venv 
    source venv/bin/activate 
fi


# Create folders 
if ! [ -d "$DIRECTORY" ]; then
    mkdir ./runpod-volume/models
    mkdir ./runpod-volume/nodes
    mkdir ./runpod-volume/workflows
fi