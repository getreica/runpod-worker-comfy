# 🚀 Runpod Serverless ComfyUI Worker

> Transform ComfyUI into a powerful and scalable serverless API with RunPod

## 🏗️ Architecture

**Core Components**
- 🎯 ComfyUI as processing backend
- ☁️ RunPod for serverless deployment
- 🔄 Customizable workflow system
- 📦 Flexible model management

## 🛠️ Setup & Installation

### Prerequisites
- `/workspace/models` directory configured with required models
- Access tokens for Huggingface and GitHub
- JSON workflow in `/workflows` folder

### Automated Build
```bash
# Step 1: Dependencies Installation
└── CUDA + Python libraries

# Step 2: ComfyUI Setup
└── Download to /comfyui
    └── Custom nodes installation
    └── Models linking: /workspace/models ➔ /comfyui/models
```

## 🎮 Usage

### Request Format
```json
{
    "webhook": "https://webhooks.yourwebsite.com",
    "request": {
        "image": "https://placehold.co/600x400",
        "comfydeploy_image_key_in_workflow": 12,
        "integer_value_key": 123,
        "text_value_key": "hello",
        "float_value_key": 23.50,
        "image_batch_key": ["image.jpg", "asdcas.jpgg"],
        "boolean_key": false
    }
}
```

## ⚙️ Configuration

### Essential Environment Variables
| Variable | Description | Example |
|----------|-------------|---------|
| VERSION | Workflow/endpoint version | `'01'` |
| HUGGINGFACE_ACCESS_TOKEN | Huggingface token | `'hf_xxxxxx'` |
| GITHUB_TOKEN | GitHub token | `'github_pat_xxxxx'` |

## ⚠️ Important Notes
- Pre-download all models to `/workspace/models`
- Use Cloud Sync for model synchronization
- Verify custom nodes compatibility

## 🤝 Credits & Community
- 🔧 [ComfyUIDeploy](https://github.com/BennyKok/comfyui-deploy)
- 🎨 [ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- ☁️ [RunPod](https://www.runpod.io/)
- 🛠️ [BLIB-LA](https://github.com/blib-la/runpod-worker-comfy)

---
*Powered by RunPod Serverless - Deploy, Scale, Create*