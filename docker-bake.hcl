variable "DOCKERHUB_REPO" {
  default = "alexgenovese"
}

variable "DOCKERHUB_IMG" {
  default = "runpod-worker-comfy"
}

variable "VERSION" {
  default = "latest"
}

variable "HUGGINGFACE_ACCESS_TOKEN" {
  default = ""
}

group "default" {
  targets = ["base"]
}

target "base" {
  context = "."
  dockerfile = "Dockerfile"
  target = "base"
  platforms = ["linux/amd64"]
  tags = ["${DOCKERHUB_REPO}/${DOCKERHUB_IMG}:${VERSION}"]
  args = {
    GITHUB_TOKEN = "${BLIBLA_SEMANTIC_RELEASE}"
    VERSION = "${VERSION}"
    HUGGINGFACE_ACCESS_TOKEN = "${HUGGINGFACE_ACCESS_TOKEN}"
  }
}
