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
    mkdir ./data/models
    mkdir ./data/nodes
    mkdir ./data/workflows
fi