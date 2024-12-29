import runpod
from runpod.serverless.utils import rp_upload
from runpod.serverless.modules.rp_logger import RunPodLogger
import json, time, os, requests, base64
from io import BytesIO
import urllib.request
import urllib.parse
from urllib.parse import urlparse

# Time to wait between API check attempts in milliseconds
COMFY_API_AVAILABLE_INTERVAL_MS = 50
# Maximum number of API check attempts
COMFY_API_AVAILABLE_MAX_RETRIES = 500
# Time to wait between poll attempts in milliseconds
COMFY_POLLING_INTERVAL_MS = int(os.environ.get("COMFY_POLLING_INTERVAL_MS", 250))
# Maximum number of poll attempts
COMFY_POLLING_MAX_RETRIES = int(os.environ.get("COMFY_POLLING_MAX_RETRIES", 500))
# Host where ComfyUI is running
COMFY_HOST = "127.0.0.1:8188"
# Enforce a clean state after each job is done
# see https://docs.runpod.io/docs/handler-additional-controls#refresh-worker
REFRESH_WORKER = os.environ.get("REFRESH_WORKER", "false").lower() == "true"


logger = RunPodLogger()


def validate_input(job_input):
    """
    Validates the input for the handler function.

    Args:
        job_input (dict): The input data to validate.

    Returns:
        tuple: A tuple containing the validated data and an error message, if any.
               The structure is (validated_data, error_message).
    """
    # Validate if job_input is provided
    if job_input is None:
        return None, "Please provide input"

    # Check if input is a string and try to parse it as JSON
    if isinstance(job_input, str):
        try:
            job_input = json.loads(job_input)
        except json.JSONDecodeError:
            return None, "Invalid JSON format in input"

    # Validate 'workflow' in input
    workflow = job_input.get("workflow")
    if workflow is None:
        return None, "Missing 'workflow' parameter" 
    
    # Check if file exists
    workflow = os.path.join("/comfyui/workflows", workflow)
    if not os.path.isfile(workflow):
        return None, f"Missing 'workflow' file in storage ${workflow}" 

    # Validate request 
    request = job_input.get("request")
    
    ## TODO validare il tipo per ogni valore delle chiavi


    # Return validated data and no error
    return job_input, None


def check_server(url, retries=500, delay=50):
    """
    Check if a server is reachable via HTTP GET request

    Args:
    - url (str): The URL to check
    - retries (int, optional): The number of times to attempt connecting to the server. Default is 50
    - delay (int, optional): The time in milliseconds to wait between retries. Default is 500

    Returns:
    bool: True if the server is reachable within the given number of retries, otherwise False
    """

    for i in range(retries):
        try:
            response = requests.get(url)

            # If the response status code is 200, the server is up and running
            if response.status_code == 200:
                print(f"runpod-worker-comfy - API is reachable")
                return True
        except requests.RequestException as e:
            # If an exception occurs, the server may not be ready
            pass

        # Wait for the specified delay before retrying
        time.sleep(delay / 1000)

    print(
        f"runpod-worker-comfy - Failed to connect to server at {url} after {retries} attempts."
    )
    return False


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def upload_images(request):
    """
    Upload a list of base64 encoded images to the ComfyUI server using the /upload/image endpoint.

    Args:
        request (json)

    Returns:
        list: A list of responses from the server for each image upload.
    """
    images = []
    for key in request:
        if type(request[key]) == str:
            # print(f"{type(request[key])}")
            if is_valid_url(request[key]):
                print(f'Valid URL: {request[key]}')
                images.append(request[key])


    if len(images) == 0:
        return {"status": "success", "message": "No images to upload", "details": []}

    responses = []
    upload_errors = []

    print(f"runpod-worker-comfy - image(s) upload")

    for image in images:
        # Get the file name
        a = urlparse(image)
        name = os.path.basename(a.path)

        # Download the image
        response = requests.get(image)
        blob = BytesIO(response.content)

        # Prepare the form data
        files = {
            "image": (name, BytesIO(blob), "image/png"),
            "overwrite": (None, "true"),
        }

        # POST request to upload the image
        response = requests.post(f"http://{COMFY_HOST}/upload/image", files=files)
        if response.status_code != 200:
            upload_errors.append(f"Error uploading {name}: {response.text}")
        else:
            responses.append(f"Successfully uploaded {name}")

    if upload_errors:
        print(f"runpod-worker-comfy - image(s) upload with errors")
        return {
            "status": "error",
            "message": "Some images failed to upload",
            "details": upload_errors,
        }

    print(f"runpod-worker-comfy - image(s) upload complete")
    return {
        "status": "success",
        "message": "All images uploaded successfully",
        "details": responses,
    }


def queue_workflow(workflow):
    """
    Queue a workflow to be processed by ComfyUI

    Args:
        workflow (dict): A dictionary containing the workflow to be processed

    Returns:
        dict: The JSON response from ComfyUI after processing the workflow
    """

    # The top level element "prompt" is required by ComfyUI
    data = json.dumps({"prompt": workflow}).encode("utf-8")

    req = urllib.request.Request(f"http://{COMFY_HOST}/prompt", data=data)
    return json.loads(urllib.request.urlopen(req).read())


def get_history(prompt_id):
    """
    Retrieve the history of a given prompt using its ID

    Args:
        prompt_id (str): The ID of the prompt whose history is to be retrieved

    Returns:
        dict: The history of the prompt, containing all the processing steps and results
    """
    with urllib.request.urlopen(f"http://{COMFY_HOST}/history/{prompt_id}") as response:
        return json.loads(response.read())


def base64_encode(img_path):
    """
    Returns base64 encoded image.

    Args:
        img_path (str): The path to the image

    Returns:
        str: The base64 encoded image
    """
    with open(img_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return f"{encoded_string}"


def process_output_images(outputs, job_id):
    """
    This function takes the "outputs" from image generation and the job ID,
    then determines the correct way to return the image, either as a direct URL
    to an AWS S3 bucket or as a base64 encoded string, depending on the
    environment configuration.

    Args:
        outputs (dict): A dictionary containing the outputs from image generation,
                        typically includes node IDs and their respective output data.
        job_id (str): The unique identifier for the job.

    Returns:
        dict: A dictionary with the status ('success' or 'error') and the message,
              which is either the URL to the image in the AWS S3 bucket or a base64
              encoded string of the image. In case of error, the message details the issue.

    The function works as follows:
    - It first determines the output path for the images from an environment variable,
      defaulting to "/comfyui/output" if not set.
    - It then iterates through the outputs to find the filenames of the generated images.
    - After confirming the existence of the image in the output folder, it checks if the
      AWS S3 bucket is configured via the BUCKET_ENDPOINT_URL environment variable.
    - If AWS S3 is configured, it uploads the image to the bucket and returns the URL.
    - If AWS S3 is not configured, it encodes the image in base64 and returns the string.
    - If the image file does not exist in the output folder, it returns an error status
      with a message indicating the missing image file.
    """

    # The path where ComfyUI stores the generated images
    COMFY_OUTPUT_PATH = os.environ.get("COMFY_OUTPUT_PATH", "/comfyui/output")

    output_images = {}

    for node_id, node_output in outputs.items():
        if "images" in node_output:
            for image in node_output["images"]:
                output_images = os.path.join(image["subfolder"], image["filename"])

    print(f"runpod-worker-comfy - image generation is done")

    # expected image output folder
    local_image_path = f"{COMFY_OUTPUT_PATH}/{output_images}"

    print(f"runpod-worker-comfy - {local_image_path}")

    # The image is in the output folder
    if os.path.exists(local_image_path):
        if os.environ.get("BUCKET_ENDPOINT_URL", False):
            # URL to image in AWS S3
            image = rp_upload.upload_image(job_id, local_image_path)
            print(
                "runpod-worker-comfy - the image was generated and uploaded to AWS S3"
            )
        else:
            # base64 image
            image = base64_encode(local_image_path)
            print(
                "runpod-worker-comfy - the image was generated and converted to base64"
            )

        return {
            "status": "success",
            "message": image,
        }
    else:
        print("runpod-worker-comfy - the image does not exist in the output folder")
        return {
            "status": "error",
            "message": f"the image does not exist in the specified output folder: {local_image_path}",
        }


# Check if the key exists in input request
# return the value changed
def change_value(value, input): 
    key = value['inputs']['input_id']
    
    if key in input['request']: 
        print(f"---> Changing value {key} in {input['request'][key]}  <----")
        value['inputs']['default_value'] = input['request'][key]

    # ritorna l'oggetto json aggiornato
    return value
                  

# Filter only the keys we need to change
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


def handler(job_input):
    """
    The main function that handles a job of generating an image.

    This function validates the input, sends a prompt to ComfyUI for processing,
    polls ComfyUI for result, and retrieves generated images.

    Args:
        job (dict): A dictionary containing job details and input parameters.

    Returns:
        dict: A dictionary containing either an error message or a success status with generated images.
    """

    # Make sure that the input is valid
    validated_data, error_message = validate_input(job_input)
    if error_message:
        return {"error": error_message}

    # Extract validated data
    request = validated_data.get("request") # json 
    
    # Upload images if they exist
    upload_result = upload_images(request)
    if upload_result["status"] == "error":
        return upload_result
    

    # Read JSON object
    endpoint_version = os.environ['VERSION']
    workflow = json.load(os.path.join("/", "snapshots", f"version_{endpoint_version}.json"))
    print(f"--- Reading workflow file in {workflow}")

    # Extract all nodes with of ComfyDeploy Class
    # check if input_id == chiave presente nel json text 
    # se si, merge json con i nuovi valori 
    values = workflow.values()
    workflow = merge_values(values, workflow)


    # Queue the workflow
    try:
        queued_workflow = queue_workflow(workflow)
        prompt_id = queued_workflow["prompt_id"]
        print(f"runpod-worker-comfy - queued workflow with ID {prompt_id} -- queued_workflow: {queued_workflow}")
    except Exception as e:
        return {"error": f"Error queuing workflow: {str(e)}"}

    # Poll for completion
    print(f"runpod-worker-comfy - wait until image generation is complete")
    retries = 0
    try:
        while retries < COMFY_POLLING_MAX_RETRIES:
            history = get_history(prompt_id)

            # Exit the loop if we have found the history
            if prompt_id in history and history[prompt_id].get("outputs"):
                break
            else:
                # Wait before trying again
                time.sleep(COMFY_POLLING_INTERVAL_MS / 1000)
                retries += 1
        else:
            return {"error": "Max retries reached while waiting for image generation"}
    except Exception as e:
        return {"error": f"Error waiting for image generation: {str(e)}"}

    # Get the generated image and return it as URL in an AWS bucket or as base64 
    # TODO job id al posto del prompt id
    images_result = process_output_images(history[prompt_id].get("outputs"), prompt_id)

    result = {**images_result, "refresh_worker": REFRESH_WORKER}

    # {
    #   "status": "success",
    #    "message": [ base64(image), base64(image)],
    # }

    return result


# Start the handler only if this script is run directly
if __name__ == "__main__":
    # Make sure that the ComfyUI API is available
    check_server(
        f"http://{COMFY_HOST}",
        COMFY_API_AVAILABLE_MAX_RETRIES,
        COMFY_API_AVAILABLE_INTERVAL_MS,
    )
    logger.info('ComfyUI API is ready')
    logger.info('Starting RunPod Serverless...')
    runpod.serverless.start({
        "handler": handler,
        # "return_aggregate_stream": True,  # Optional: Aggregate results are accessible via /run endpoint
    })