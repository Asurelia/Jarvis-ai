"""
Configuration optimisée pour GPU AMD RX 7800 XT
"""
import os
import cv2

# Configuration pour AMD RX 7800 XT avec ROCm
os.environ['HSA_OVERRIDE_GFX_VERSION'] = '11.0.0'  # Pour ROCm
os.environ['OLLAMA_NUM_GPU'] = '999'  # Utiliser tout le GPU
os.environ['OLLAMA_GPU_LAYERS'] = '35'  # Pour modèles 7B

# Configuration OpenCV avec OpenCL pour AMD
def configure_amd_gpu():
    """Configure OpenCV pour utiliser le GPU AMD"""
    if cv2.ocl.haveOpenCL():
        cv2.ocl.setUseOpenCL(True)
        print("✅ OpenCL détecté et activé pour AMD GPU")
        return True
    else:
        print("⚠️  OpenCL non disponible")
        return False

# Configuration Ollama pour AMD
OLLAMA_CONFIG = {
    "models": {
        "vision": "llava:7b",
        "coding": "qwen2.5-coder:7b", 
        "autocomplete": "deepseek-coder:1.3b"
    },
    "gpu_memory_fraction": 0.8,  # Utiliser 80% de la VRAM
    "batch_size": 4,
    "num_threads": 8
}