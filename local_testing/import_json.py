import json, os, requests
from urllib.parse import urlparse
from io import BytesIO

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
#
#       INPUT
#
with open('./demo_input.json') as fp:
        input = json.load(fp)


def get_images(input): 
    for key in input['request']:
        if type(input['request'][key]) == str:
            print(f"{type(input['request'][key])}")
            if is_valid_url(input['request'][key]):
                print(f'Valid URL: {input['request'][key]}')

                # Get the file name
                a = urlparse(input['request'][key])
                name = os.path.basename(a.path)

                # Download the image
                response = requests.get(input['request'][key])
                blob = BytesIO(response.content)
                
                # Encode Base64
                print(f"{name} ---------- {blob}")


get_images(input)



#
#       WORKFLOW in STORAGE
#
with open('../data/workflows/prompt/version_01.json') as fp:
    workflow = json.load(fp)

# Check if the key exists in input request
# return the value changed
def change_value(value, input): 
    key = value['inputs']['input_id']
    
    if key in input['request']: 
        print(f"---> Changing value {key} in {input['request'][key]}  <----")
        value['inputs']['default_value'] = input['request'][key]

    # ritorna l'oggetto json aggiornato
    return value
                  

values = workflow.values()

# Filter and only the key that we need to change
# Change the value of the key that match into input keys
def merge_values(values, input): 
    for value in values:
        # Currently using Comfydeploy module: https://github.com/BennyKok/comfyui-deploy/blob/main/comfy-nodes/external_boolean.py
        key_to_check = value['class_type']
        if key_to_check == "ComfyUIDeployExternalText":          
            value = change_value(value, input)
        if key_to_check == "ComfyUIDeployExternalTextAny":          
            value = change_value(value, input)
        if key_to_check == "ComfyUIDeployExternalImage":           # Legge sia URL che local Path 
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalNumberInt":      
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalNumber":         
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalLora":            
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalImageBatch":
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalImageAlpha":
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalFaceModel":
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalVideo":
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalCheckpoint":
            value = change_value(value, input)
        elif key_to_check == "ComfyUIDeployExternalBoolean":
            value = change_value(value, input)
    
    return values
        
