from collections import deque
from urllib.parse import urlparse
import os, hashlib, shutil, subprocess, time, json
from huggingface_hub import hf_hub_download, login

class WeightsDownloadCache:
    def __init__(
        self, min_disk_free: int = 10 * (2**30), base_dir: str = "/comfyui", version = '01'
    ):
        """
        WeightsDownloadCache is meant to track and download weights files as fast
        as possible, while ensuring there's enough disk space.

        It tries to keep the most recently used weights files in the cache, so
        ensure you call ensure() on the weights each time you use them.

        It will not re-download weights files that are already in the cache.

        :param min_disk_free: Minimum disk space required to start download, in bytes.
        :param base_dir: The base directory to store weights files.
        """
        self.min_disk_free = min_disk_free
        self.base_dir = base_dir
        self._hits = 0
        self._misses = 0
        self.BASE_WEIGHT_FOLDER = base_dir + '/models'
        self.BASE_NODES_FOLDER = base_dir + '/custom_nodes'

        # TODO - Env variables
        self.hf_account = os.environ.get("HF_ACCOUNT", "alexgenovese")
        self.hf_token = os.environ.get("HF_TOKEN", "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")
        self.version = os.environ.get("VERSION", version)

        print(f"Setting up environment to version {self.version}")

        # Least Recently Used (LRU) cache for paths
        self.lru_paths = deque()


    def _remove_least_recent(self) -> None:
        """
        Remove the least recently used weights file from the cache and disk.
        """
        oldest = self.lru_paths.popleft()
        self._rm_disk(oldest)

    def cache_info(self) -> str:
        """
        Get cache information.

        :return: Cache information.
        """

        return f"CacheInfo(hits={self._hits}, misses={self._misses}, base_dir='{self.base_dir}', currsize={len(self.lru_paths)})"

    def _rm_disk(self, path: str) -> None:
        """
        Remove a weights file or directory from disk.
        :param path: Path to remove.
        """
        if os.path.isfile(path):
            os.remove(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

    def _has_enough_space(self) -> bool:
        """
        Check if there's enough disk space.

        :return: True if there's more than min_disk_free free, False otherwise.
        """
        disk_usage = shutil.disk_usage(self.base_dir)
        print(f"Free disk space: {disk_usage.free}")
        return disk_usage.free >= self.min_disk_free

    def ensure(self, url: str) -> str:
        """
        Ensure weights file is in the cache and return its path.

        This also updates the LRU cache to mark the weights as recently used.

        :param url: URL to download weights file from, if not in cache.
        :return: Path to weights.
        """
        path = self.weights_path(url)

        if path in self.lru_paths:
            # here we remove to re-add to the end of the LRU (marking it as recently used)
            self._hits += 1
            self.lru_paths.remove(path)
        else:
            self._misses += 1
            self.download_weights(url, path)

        self.lru_paths.append(path)  # Add file to end of cache
        return path

    def weights_path(self, url: str) -> str:
        """
        Generate path to store a weights file based hash of the URL.

        :param url: URL to download weights file from.
        :return: Path to store weights file.
        """
        hashed_url = hashlib.sha256(url.encode()).hexdigest()
        short_hash = hashed_url[:16]  # Use the first 16 characters of the hash
        return os.path.join(self.base_dir, short_hash)

    
    def download_weights(self, url: str, dest: str) -> None:
        """
        Download weights file from a URL, ensuring there's enough disk space.

        :param url: URL to download weights file from.
        :param dest: Path to store weights file.
        """
        print("Ensuring enough disk space...")
        while not self._has_enough_space() and len(self.lru_paths) > 0:
            self._remove_least_recent()

        print(f"Downloading weights: {url}")

        st = time.time()
        # maybe retry with the real url if this doesn't work
        try:
            output = subprocess.check_output(["pget", url, "-o", dest], close_fds=True)
            print(output)
        except subprocess.CalledProcessError as e:
            # If download fails, clean up and re-raise exception
            print(e.output)
            self._rm_disk(dest)
            raise e
        print(f"Downloaded weights in {time.time() - st} seconds")


    # Download ComfyUI and modules
    def download_custom_nodes(self):
        print("------------------ START DOWNLOADING MODULE ----------------- ")
        MODULES = ''
        # Read weights library 
        with open(f'/src/custom_nodes/version_{self.version}.json') as fp:
            MODULES = json.load(fp)
        
        modules_array = MODULES['modules']

        for module in modules_array:
            folder_name = os.path.split(module['github_url'])[1]

            if not os.path.exists(f"{self.BASE_NODES_FOLDER}/{folder_name}"):
                print(f"Download {module['github_url']} in {folder_name}")
                # Update with hash: git clone --single-branch --branch <commit-hash> https://github.com/username/repository.git
                os.system(f"git clone --recurse-submodules {module['github_url']} {self.BASE_NODES_FOLDER}/{folder_name}")
                if os.path.isfile(f"{self.BASE_NODES_FOLDER}/{folder_name}/requirements.txt"):
                    os.system(f"pip install -r {self.BASE_NODES_FOLDER}/{folder_name}/requirements.txt")
    
        print("------------------ END DOWNLOADING MODULE ----------------- ")

    # Check or Download Weight
    def download_weights(self) -> None: 
        print("------------------ START DOWNLOADING WEIGHTS ----------------- ")
        WEIGHTS = ''
        # Read weights library 
        with open(f'/src/models/version_{self.version}.json') as fp:
            WEIGHTS = json.load(fp)

        # login into HF with token 
        login(token=self.hf_token)

        try: 
            folder_weight_arr = WEIGHTS.keys()
            for folder_name in folder_weight_arr:
                # Creating local vars 
                folder_path = self.BASE_WEIGHT_FOLDER + "/" + folder_name
                array_weights = WEIGHTS[folder_name]

                # replace string - with _
                if "-" in folder_name:
                    folder_name = folder_name.replace("-", "_")

                # Create if not exists 
                if not os.path.exists( self.BASE_WEIGHT_FOLDER + "/" + folder_name ):
                    os.makedirs( self.BASE_WEIGHT_FOLDER + "/" + folder_name )

                # Download all weights of folder_name
                for weight in array_weights:
                    filename = os.path.basename(weight['url']) 

                    # Subfolder exists 
                    if 'folder' in weight.keys():
                        # Create subfolder in directory if not exists
                        if not os.path.exists( self.BASE_WEIGHT_FOLDER + "/" + weight['folder'] ): 
                            os.makedirs( self.BASE_WEIGHT_FOLDER + "/" + weight['folder'] )
                        folder_path = self.BASE_WEIGHT_FOLDER + "/" + weight['folder']

                    # Check if file exists 
                    if not os.path.isfile(  folder_path + "/" + filename ):
                        print(f"Downaloding {weight['url']} in {folder_path}")
                        
                        self.downloader(
                            url=weight['url'],
                            params={
                                'local_dir' : folder_path
                            }
                        )
            print("------------------ END DOWNLOADING WEIGHTS ----------------- ")

        except Exception as error:
             print("-> download_weights_lib | Exception: ", error)


    # Download using huggingface_hub_download func or with aria2c
    def downloader(self, url : str = None, params = None ) -> bool:
        if url is None or "":
            raise Exception("No url passed in params - download_weights")
        
        try: 
            filename = os.path.basename(url)

            if "huggingface.co" in url: 
                repo_id = self.hf_account + "/" + self.get_hf_repo_from_url(url)
                local_dir = params['local_dir']

                hf_hub_download(
                    repo_id=repo_id,
                    filename=filename,
                    local_dir=local_dir,
                    local_dir_use_symlinks=False, # download the file
                )

            else: 
                destination = os.path.join(params['local_dir'], filename)
                os.system(f"aria2c -o {destination} {url}")

            return True
        
        except Exception as error:
             print("--> download_weight | Exception: ", error)
             return False
 
    # get repo_id from url
    def get_hf_repo_from_url(self, hf_url: str = None) -> str: 
        if hf_url is None:
            raise Exception("No url passed")
        
        repo_path = urlparse(hf_url).path
        repo_path = repo_path.rsplit("/", 3)[:1]
        repo_path = repo_path[0][1:]
        
        return repo_path



if __name__ == "__main__":
    # TODO add into Env variables
    weights = WeightsDownloadCache()
    
    # Download Custom Nodes
    weights.download_custom_nodes()
    
    # Download Weights 
    weights.download_weights()
