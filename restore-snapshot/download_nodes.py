import json, os, subprocess, requests 
from urllib.request import urlopen

#
#   Get last has commit in each repo
#
def get_commit_hash(repo_url, target_dir, token):
    # Check if the repo_url is an SSH URL or HTTPS URL
    if repo_url.startswith("git@github.com:"):
        print("This function uses HTTPS with a personal access token. Please provide an HTTPS URL.")
        return None
    elif repo_url.startswith("https://github.com/"):
        # For HTTPS URL, extract the repo name by removing the 'https://github.com/' prefix
        repo_name = repo_url.replace("https://github.com/", "").replace(".git", "")
    else:
        print(f"Invalid GitHub URL format: {repo_url}")
        return None
    
    # Prepare the headers for GitHub API request with the token
    headers = {"Authorization": f"Bearer {token}"}
    
    # Build the GitHub API URL to fetch commits
    api_url = f"https://api.github.com/repos/{repo_name}/commits"

    target_dir = os.path.join(target_dir, repo_url.rsplit('/', 1)[1])
    
    # Send a GET request to the GitHub API
    response = requests.get(api_url, headers=headers)
    
    # If the request is successful (status code 200)
    if response.status_code == 200:
        try:
            # Extract the commit hash from the JSON response
            commits = response.json()
            if commits:
                commit_hash = commits[0]['sha']
                print(f"Commit hash: {commit_hash}")
            else:
                print(f"No commits found for {repo_url}")
                return None
        except KeyError:
            print(f"Error parsing commit hash for {repo_url}")
            return None
    else:
        print(f"Failed to fetch data for {repo_url}: {response.status_code}")
        return None
    
    # Return the commit hash
    return commit_hash

# 
#   Get commit hash for each repo
#
def get_github_commit_hashes(json_array, target_folder, token):
    github_repos = {}
    
    for item in json_array:
        repo_url = item['url']
        commit_hash = get_commit_hash(repo_url, target_folder, token)
        
        if commit_hash:
            github_repos[repo_url] = commit_hash
    
    return github_repos

#
#   Remove duplicates
#
def remove_duplicates(json_array):
    seen = set()
    result = []
    for item in json_array:
        if item['name'] not in seen:
            seen.add(item['name'])
            result.append(item)
    return result

#
#   Remove ComfyUI official repo from the object
#
def remove_comfyui_repo(repo_list):
    # Filtra la lista rimuovendo gli elementi con 'name' uguale a 'ComfyUI'
    return [repo for repo in repo_list if repo['name'] != 'ComfyUI']

#
#   Convert Github URL into SSH
#
def convert_https_to_ssh(github_url):
    # Ensure the URL starts with 'https://github.com/'
    if github_url.startswith("https://github.com/"):
        # Remove the 'https://github.com/' part and split by '/'
        repo_info = github_url[len("https://github.com/"):].strip("/")
        # Convert to SSH format
        ssh_url = f"git@github.com:{repo_info}.git"
        return ssh_url
    else:
        raise ValueError("Invalid GitHub HTTPS URL")

#
#   Crea un elenco di nodi da scaricare per far funzionare questo workflow
#
def get_custom_nodes_to_download(workflow_local_file, remote_url, token):
    
    with open(workflow_local_file) as f:
        workflow_data = json.load(f)
    
    # Estrai i valori di "class_type"
    class_types = {item["class_type"] for item in workflow_data.values()}
    print(f"Class types: {class_types}")

    # Read the remote url repository of ComfyUI nodes
    f = urlopen(remote_url)
    remote_data = json.load(f)

    comfyui_nodes = set(remote_data["https://github.com/comfyanonymous/ComfyUI"][0])
    class_types = class_types - comfyui_nodes
    print(f"Filtered class types: {class_types}")
    
    # Cerca i nodi corrispondenti
    urls_to_download = []
    for class_type in class_types:
        for url_repo in remote_data: 
            if class_type in remote_data[url_repo][0]:
                urls_to_download.append({ "url": url_repo, "name": remote_data[url_repo][1]['title_aux'] })
            # else:
            #     print(f"Attenzione: il nodo '{class_type}' non è presente nel file remoto.")
    
    return remove_comfyui_repo(remove_duplicates(urls_to_download))


#
# Funzione per clonare o aggiornare un repository GitHub
#
def clone_or_update_repo(repo_url, commit_hash, target_dir, token=None):
    # Portami alla cartella root dove installare il nodo
    if os.path.exists(target_dir):
        print(f"Repository already exists: {target_dir}")
        os.chdir(target_dir)
        # Check if the current commit matches the desired one
        current_commit = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip().decode("utf-8")
        if current_commit == commit_hash:
            print(f"Repository already at desired commit: {commit_hash}")
            return
        else:
            print(f"Updating repository to commit {commit_hash}...")
            subprocess.run(["git", "fetch"], check=True)
            subprocess.run(["git", "checkout", commit_hash], check=True)
    else:
        # If token is provided, update the repo URL to include it
        if token:
            repo_url = repo_url.replace("https://", f"https://{token}@")
        
        print(f"Cloning repository {repo_url} into {target_dir}...")
        subprocess.run(["git", "clone", repo_url, target_dir], check=True)
        # Install requirements for this node into the node folder
        # os.chdir(target_dir)
        print(f"Running INSTALL {target_dir}/requirements.txt")
        subprocess.run(["pip3", "install", "-r", f"{target_dir}/requirements.txt"])
        #
        # TODO: checkout at specific hash
        # print(f"Checking out commit {commit_hash}...")
        # subprocess.run(["git", "checkout", commit_hash], check=True)

#
#   Read all repos and call clone_or_update_repo 
#
def download_repositories(github_repos, custom_nodes_dir, token): 
    # Scarica i repository GitHub al commit specificato
    os.makedirs(custom_nodes_dir, exist_ok=True)
    for repo_url, hash_value in github_repos.items():
        repo_name = os.path.basename(repo_url)
        target_dir = os.path.join(custom_nodes_dir, repo_name)
        
        try:
            clone_or_update_repo(repo_url, hash_value, target_dir, token)
        except subprocess.CalledProcessError as e:
            print(f"Failed to process repository {repo_url}: {e}")



#
#   Only for testing
#
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    # Percorso al file locale e URL remoto
    local_file = './workflows/version_01.json'
    remote_json_url = 'https://raw.githubusercontent.com/ltdrdata/ComfyUI-Manager/refs/heads/main/extension-node-map.json'
    github_token = os.getenv("GITHUB_TOKEN")

    # Ottieni l'elenco degli URL da scaricare
    nodes_to_download = get_custom_nodes_to_download(local_file, remote_json_url, github_token)

    # Stampa l'elenco degli URL
    print("Nodi da scaricare:")
    print(f"{nodes_to_download}")

    print("Prendi l'ultimo hash")
    custom_nodes_dir = "/ComfyUI/custom_nodes"
    github_repos = get_github_commit_hashes(nodes_to_download, target_folder=custom_nodes_dir, token=github_token)
    print(github_repos)