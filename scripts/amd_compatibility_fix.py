#!/usr/bin/env python3
"""
🔴 Script de correction automatique compatibilité AMD JARVIS
Corrige tous les services pour support GPU AMD complet
"""

import os
import re
import yaml
import subprocess
from pathlib import Path

class AMDCompatibilityFixer:
    def __init__(self, jarvis_root):
        self.jarvis_root = Path(jarvis_root)
        self.fixes_applied = []
        
    def detect_amd_gpu(self):
        """Détecte si un GPU AMD est présent"""
        try:
            # Vérifier ROCm
            result = subprocess.run(['rocm-smi'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ GPU AMD avec ROCm détecté")
                return True
        except FileNotFoundError:
            pass
            
        # Vérifier via lspci/dxdiag selon OS
        try:
            if os.name == 'posix':  # Linux
                result = subprocess.run(['lspci'], capture_output=True, text=True)
                if 'AMD' in result.stdout or 'ATI' in result.stdout:
                    print("✅ GPU AMD détecté (sans ROCm)")
                    return True
            else:  # Windows
                result = subprocess.run(['wmic', 'path', 'win32_VideoController', 'get', 'name'], 
                                      capture_output=True, text=True)
                if 'AMD' in result.stdout or 'Radeon' in result.stdout:
                    print("✅ GPU AMD détecté (Windows)")
                    return True
        except:
            pass
            
        print("⚠️ Aucun GPU AMD détecté, application des corrections préventives")
        return False

    def fix_stt_service(self):
        """Corrige le service STT pour support AMD"""
        stt_main = self.jarvis_root / 'services' / 'stt-service' / 'main.py'
        
        if not stt_main.exists():
            return
            
        with open(stt_main, 'r') as f:
            content = f.read()
        
        # Correction détection GPU
        old_device = 'DEVICE = "cuda" if torch.cuda.is_available() else "cpu"'
        new_device = '''def get_optimal_device():
    """Détection GPU optimale AMD/NVIDIA"""
    if torch.cuda.is_available():
        # Vérifier si c'est ROCm (AMD)
        try:
            device_name = torch.cuda.get_device_name(0)
            if 'AMD' in device_name or 'Radeon' in device_name:
                print("🔴 GPU AMD détecté pour STT")
                return "cuda"  # ROCm utilise l'API CUDA
        except:
            pass
        return "cuda"
    return "cpu"

DEVICE = get_optimal_device()'''

        if old_device in content:
            content = content.replace(old_device, new_device)
            
            # Correction FP16 pour AMD
            content = content.replace(
                '"fp16": DEVICE == "cuda"',
                '"fp16": DEVICE == "cuda" and "NVIDIA" in torch.cuda.get_device_name(0) if DEVICE == "cuda" else False'
            )
            
            with open(stt_main, 'w') as f:
                f.write(content)
            
            self.fixes_applied.append("STT Service - Support GPU AMD")

    def fix_tts_service(self):
        """Corrige le service TTS pour support AMD"""
        # Configuration TTS
        tts_config = self.jarvis_root / 'services' / 'tts-service' / 'utils' / 'config.py'
        if tts_config.exists():
            with open(tts_config, 'r') as f:
                content = f.read()
            
            # Améliorer détection GPU
            content = content.replace(
                'TTS_DEVICE: str = "cpu"  # ou "cuda" si GPU disponible',
                '''# Détection automatique GPU AMD/NVIDIA
def get_tts_device():
    if torch.cuda.is_available():
        device_name = torch.cuda.get_device_name(0)
        if 'AMD' in device_name or 'Radeon' in device_name:
            print("🔴 TTS utilise GPU AMD")
        return "cuda"
    return "cpu"

TTS_DEVICE: str = get_tts_device()'''
            )
            
            with open(tts_config, 'w') as f:
                f.write(content)
        
        # Moteur TTS
        tts_engine = self.jarvis_root / 'services' / 'tts-service' / 'core' / 'tts_engine.py'
        if tts_engine.exists():
            with open(tts_engine, 'r') as f:
                content = f.read()
            
            # Remplacer CUDA-specific par compatible AMD
            content = content.replace(
                'torch.cuda.empty_cache()',
                '''# Nettoyage mémoire GPU compatible AMD/NVIDIA
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    torch.cuda.synchronize()  # Meilleur support AMD'''
            )
            
            with open(tts_engine, 'w') as f:
                f.write(content)
            
        self.fixes_applied.append("TTS Service - Support GPU AMD")

    def fix_docker_configs(self):
        """Corrige les configurations Docker pour GPU AMD"""
        docker_files = [
            'docker-compose.ai-pod.yml',
            'docker-compose.audio-pod.yml',
            'docker-compose.yml'
        ]
        
        for docker_file in docker_files:
            docker_path = self.jarvis_root / docker_file
            if not docker_path.exists():
                continue
                
            with open(docker_path, 'r') as f:
                content = f.read()
            
            # Remplacer runtime NVIDIA par support multi-GPU
            if 'driver: nvidia' in content:
                content = re.sub(
                    r'devices:\s*\n\s*- driver: nvidia\s*\n\s*count: \d+\s*\n\s*capabilities: \[gpu\]',
                    '''devices:
      # Support GPU AMD via ROCm
      - driver: amd.com/gpu
        count: 1
        capabilities: [gpu]
      # Fallback NVIDIA si disponible
      - driver: nvidia
        count: 1
        capabilities: [gpu]
        device_ids: ['0']''',
                    content,
                    flags=re.MULTILINE
                )
            
            # Activer GPU pour audio si AMD disponible
            if 'GPU_ENABLED=false' in content:
                content = content.replace(
                    'GPU_ENABLED=false',
                    'GPU_ENABLED=${AMD_GPU_AVAILABLE:-false}'
                )
            
            with open(docker_path, 'w') as f:
                f.write(content)
            
        self.fixes_applied.append("Docker - Support GPU AMD multi-runtime")

    def fix_requirements(self):
        """Met à jour les requirements pour support AMD"""
        req_files = list(self.jarvis_root.rglob('requirements.txt'))
        
        for req_file in req_files:
            with open(req_file, 'r') as f:
                content = f.read()
            
            modified = False
            
            # Remplacer FAISS CPU par GPU si brain-api
            if 'brain-api' in str(req_file) and 'faiss-cpu' in content:
                content = content.replace(
                    'faiss-cpu==1.7.4',
                    '''# FAISS avec support GPU AMD/NVIDIA
faiss-gpu==1.7.4; sys_platform == "linux"
faiss-cpu==1.7.4; sys_platform != "linux"'''
                )
                modified = True
            
            # Ajouter PyTorch ROCm si nécessaire
            if 'torch==' in content and 'rocm' not in content:
                torch_lines = [line for line in content.split('\n') if 'torch==' in line]
                for torch_line in torch_lines:
                    version = re.search(r'torch==([0-9.]+)', torch_line)
                    if version:
                        v = version.group(1)
                        new_line = f'''# PyTorch avec support AMD ROCm
{torch_line}
torch=={v}+rocm5.6; sys_platform == "linux" and platform_machine == "x86_64"'''
                        content = content.replace(torch_line, new_line)
                        modified = True
            
            if modified:
                with open(req_file, 'w') as f:
                    f.write(content)
        
        self.fixes_applied.append("Requirements - PyTorch ROCm + FAISS GPU")

    def fix_ocr_engine(self):
        """Corrige le moteur OCR pour meilleur support AMD"""
        ocr_engine = self.jarvis_root / 'core' / 'vision' / 'ocr_engine.py'
        
        if not ocr_engine.exists():
            return
            
        with open(ocr_engine, 'r') as f:
            content = f.read()
        
        # Améliorer détection GPU pour EasyOCR
        content = content.replace(
            'self.reader = easyocr.Reader(self.languages, gpu=True)',
            '''# Détection GPU intelligente pour EasyOCR
gpu_available = torch.cuda.is_available()
if gpu_available:
    try:
        device_name = torch.cuda.get_device_name(0)
        if 'AMD' in device_name:
            print("🔴 OCR utilise GPU AMD")
        self.reader = easyocr.Reader(self.languages, gpu=True)
    except Exception as e:
        print(f"⚠️ Fallback OCR CPU: {e}")
        self.reader = easyocr.Reader(self.languages, gpu=False)
else:
    self.reader = easyocr.Reader(self.languages, gpu=False)'''
        )
        
        with open(ocr_engine, 'w') as f:
            f.write(content)
            
        self.fixes_applied.append("OCR Engine - Détection GPU AMD améliorée")

    def create_amd_env_template(self):
        """Crée un template d'environnement AMD"""
        env_template = self.jarvis_root / '.env.amd'
        
        content = '''# 🔴 Configuration JARVIS pour GPU AMD
# Variables d'environnement pour optimisation AMD

# GPU AMD
AMD_GPU_AVAILABLE=true
ROCM_VERSION=5.6
HIP_VISIBLE_DEVICES=0

# Performance
FORCE_AMD_OPTIMIZATION=true
AMD_QUALITY_LEVEL=4
DISABLE_HEAVY_POST_PROCESSING=false

# PyTorch ROCm
PYTORCH_ROCM_ARCH=gfx1030  # Adapter à votre GPU
HSA_OVERRIDE_GFX_VERSION=11.0.0

# Services
OLLAMA_GPU_ENABLED=true
OLLAMA_NUM_GPU=1
STT_GPU_ENABLED=true
TTS_GPU_ENABLED=true
OCR_GPU_ENABLED=true

# Docker
COMPOSE_FILE=docker-compose.yml:docker-compose.amd.yml
GPU_RUNTIME=rocm

# Monitoring
ENABLE_GPU_MONITORING=true
LOG_GPU_PERFORMANCE=true

# Fallbacks
ENABLE_CPU_FALLBACK=true
AUTO_QUALITY_ADJUSTMENT=true
'''
        
        with open(env_template, 'w') as f:
            f.write(content)
            
        self.fixes_applied.append(".env.amd - Template configuration AMD")

    def create_amd_docker_override(self):
        """Crée un override Docker pour AMD"""
        override_content = '''# 🔴 Docker Compose override pour GPU AMD
version: '3.8'

services:
  brain-api:
    environment:
      - CUDA_VISIBLE_DEVICES=0
      - HIP_VISIBLE_DEVICES=0
      - ROCM_VERSION=5.6
    deploy:
      resources:
        reservations:
          devices:
            - driver: amd.com/gpu
              count: 1
              capabilities: [gpu]

  stt-service:
    environment:
      - GPU_ENABLED=true
      - DEVICE=cuda  # ROCm utilise API CUDA
    deploy:
      resources:
        reservations:
          devices:
            - driver: amd.com/gpu
              capabilities: [gpu]

  tts-service:
    environment:
      - TTS_GPU_ENABLED=true
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: amd.com/gpu
              capabilities: [gpu]

  ollama:
    environment:
      - OLLAMA_GPU_LAYERS=35
      - ROCM_VERSION=5.6
    deploy:
      resources:
        reservations:
          devices:
            - driver: amd.com/gpu
              count: 1
              capabilities: [gpu]
'''
        
        override_path = self.jarvis_root / 'docker-compose.amd.yml'
        with open(override_path, 'w') as f:
            f.write(override_content)
            
        self.fixes_applied.append("docker-compose.amd.yml - Override AMD")

    def run_all_fixes(self):
        """Execute toutes les corrections"""
        print("🔴 Début correction compatibilité AMD JARVIS...")
        
        amd_detected = self.detect_amd_gpu()
        
        self.fix_stt_service()
        self.fix_tts_service() 
        self.fix_docker_configs()
        self.fix_requirements()
        self.fix_ocr_engine()
        self.create_amd_env_template()
        self.create_amd_docker_override()
        
        print(f"\n✅ Corrections AMD appliquées:")
        for fix in self.fixes_applied:
            print(f"  ✓ {fix}")
            
        print(f"\n📋 Étapes suivantes:")
        print("  1. Installer ROCm: https://rocm.docs.amd.com/")
        print("  2. Copier .env.amd vers .env et adapter")
        print("  3. Redémarrer avec: docker-compose -f docker-compose.yml -f docker-compose.amd.yml up")
        print("  4. Vérifier logs GPU dans l'interface")

if __name__ == "__main__":
    import sys
    
    jarvis_root = sys.argv[1] if len(sys.argv) > 1 else "."
    fixer = AMDCompatibilityFixer(jarvis_root)
    fixer.run_all_fixes()