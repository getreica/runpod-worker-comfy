import os, time, asyncio, argparse
from download_nodes import get_custom_nodes_to_download, get_github_commit_hashes, download_repositories

BASE_COMFYUI_PATH = "/comfyui"

class DownloadAssets:
    # Initialize the class
    def __init__(self, workflow_path: str, token = str ):
        self.workflow_path = workflow_path
        self.extensions = ['.pth', '.safetensors', '.bin', '.sft']
        self.token = token
        # Directory where to download the custom nodes
        self.custom_nodes_dir = f"{BASE_COMFYUI_PATH}/custom_nodes"
        # ComfyUI nodes repository
        self.remote_nodes_list = 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/refs/heads/main/extension-node-map.json'

    # Mappatura URL del repository GitHub e hash del commit
    # github_repos = {
    #     "https://github.com/example-user/example-repo.git": "abcdef1234567890abcdef1234567890abcdef12", 
    #     "https://github.com/another-user/another-repo.git": "1234567890abcdef1234567890abcdef12345678"
    # }
    # Download all nodes if hash is different. Always the latest version.
    # TODO: pass the hash
    def download_nodes(self):        
        # Get URL list to download
        try:
            print(f"--------------- Downloading nodes from {self.remote_nodes_list}")
            github_repos = get_custom_nodes_to_download(self.workflow_path, self.remote_nodes_list, self.token)
            print(f"--------------- Downloading nodes from {self.custom_nodes_dir}")
            github_repos = get_github_commit_hashes(github_repos, self.custom_nodes_dir, self.token)
            print(f"--------------- Downloading nodes from {self.custom_nodes_dir}")
            download_repositories( github_repos, self.custom_nodes_dir, self.token )
        except Exception as e:
            raise Exception(f"!!!!!! download_nodes issue: {e}")

    
    # Start node download
    def start(self):
        print(f"\n --------------- --------------- Start downloading nodes")
        start_time = time.time()

        # Run the async download
        self.download_nodes()

        end_time = time.time()
        print(f"\n --------------- --------------- Total download time: {end_time - start_time:.2f} seconds")


#
#   Entrypoint
#
if __name__ == "__main__":
    # Create Argparse 
    parser = argparse.ArgumentParser(description='Downloader ComfyUI Workflow file')
    #
    # Define input params
    #
    parser.add_argument('--version', action="store", dest='version', default="01")
    parser.add_argument('--github_token', action="store", dest='github_token', default="")
    
    models_dir = f"{BASE_COMFYUI_PATH}/models"
    custom_nodes_dir = f"{BASE_COMFYUI_PATH}/custom_nodes"

    # Now, parse the command line arguments and store the 
    # values in the `args` variable
    args = parser.parse_args()

    # Check input param requirements
    if not args.version:
        raise ValueError('Endpoint version is missing')

    if not args.github_token:
        raise ValueError('Github token is missing')
    
    # Get Workflow
    workflow_path = os.path.join( '/', 'snapshots', f'version_{args.version}.json')

    print(f"Workflow path: {workflow_path}")
    
    # Start downloader
    downloader = DownloadAssets(workflow_path, args.github_token)
    downloader.start()