#!/usr/bin/env bash

# build with latest tag
docker build -t alexgenovese/template-comfyui-serverless .

# Publish on hub 
docker push alexgenovese/template-comfyui-serverless