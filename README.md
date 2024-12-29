# Runpod Serverless ComfyUI Worker 

> [ComfyUI](https://github.com/comfyanonymous/ComfyUI) as a serverless API on [RunPod](https://www.runpod.io/)

**[ Build step ]**
- Install Cuda and Python libraries and clean to remove unused files
- Download ComfyUI in /comfyui
- Read the embedded workflow in the /snapshots folder and 
- - download all nodes and found in JSON workflow in custom_nodes folders in /comfyui
- Link /workspace/models to /comfyui/models (here you can add your own models)


**[ Running step ]**
- Start ComfyUI ready for the inference
- Load the workflow from /snapshots folder
- - identify all nodes with the class_type "ComfyUIDeployExternal" as input variables
- - merge the JSON with the input request
- - queue the workflow 
- Start the inference 


## Request to send
```
{
    "webhook": "https://webhooks.getreica.com",
    "request" :{
        "image" : "https://placehold.co/600x400",
        "chiave_comfydeploy_image_nel_workflow" : 12,
        "chiave_valore_intero" : 123,
        "chiave_valore_testo" : "ciao",
        "chiave_valore_float" : 23.50,
        "chiave_image_batch" : [ "image.jpg", "asdcas.jpgg"],
        "chiave_boolean" : false
    }
}

```

## ⚠ MODELS folder must be downloaded before starting ⚠
A requirements to start this docker is to pre-download all models of ComfyUI into **/workspace/models** – I usually use Cloud Sync to update consistenly and avoid issue or duplications.


## ENVIRONMENT VARIABLES TO BUILD
- VERSION: the version of the workflow to load
- VERSION: the version of the endpoint
- HUGGINGFACE_ACCESS_TOKEN: the token to login into Huggingface
- GITHUB_TOKEN: the token to login into Github


## ENVIRONMENT VARIABLES FOR GITHUB ACTION

The **VERSION** manage different workflow versions you store into /snapshots. This is helpful to move forward or rollback to the prev version easily. 
```
VERSION='01'
```
-----

**HUGGINGFACE_ACCESS_TOKEN** is used to download the models from Huggingface in case some nodes need it.
```
HUGGINGFACE_ACCESS_TOKEN='hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```
-----

**GITHUB_TOKEN** is used to download the nodes from Github all nodes found in the JSON workflow file.
```
GITHUB_TOKEN='github_pat_11AADHOQI0xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

## Credits 
- [ComfyUIDeploy](https://github.com/BennyKok/comfyui-deploy) for the nodes
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) for the ComfyUI
- [RunPod](https://www.runpod.io/) for the serverless API
- [BLIB-LA](https://github.com/blib-la/runpod-worker-comfy) for the RunPod Serverless ComfyUI Worker 