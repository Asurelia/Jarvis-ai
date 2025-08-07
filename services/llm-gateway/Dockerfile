# Dockerfile optimisé pour LLM Gateway avec support AMD ROCm
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="JARVIS AI Team"
LABEL description="LLM Gateway optimisé AMD RX 7800 XT"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Variables ROCm optimisées pour AMD RX 7800 XT
ENV HIP_VISIBLE_DEVICES=0 \
    ROCR_VISIBLE_DEVICES=0 \
    HIP_FORCE_DEV_KERNARG=1 \
    AMD_LOG_LEVEL=2 \
    HIP_LAUNCH_BLOCKING=0 \
    HSA_ENABLE_INTERRUPT=0 \
    HIP_DEVICE_ORDER=PCI_BUS_ID \
    GPU_MAX_HW_QUEUES=4 \
    GPU_OPTIMIZATION=true

# Installation dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg2 \
    software-properties-common \
    lsb-release \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Tentative installation ROCm (optionnel)
RUN wget -q -O - https://repo.radeon.com/rocm/rocm.gpg.key | apt-key add - || true && \
    echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/5.7/ ubuntu main' | tee /etc/apt/sources.list.d/rocm.list || true && \
    apt-get update || true && \
    apt-get install -y rocm-smi || echo "ROCm installation failed, continuing..." && \
    rm -rf /var/lib/apt/lists/*

# Créer utilisateur non-root
RUN useradd --create-home --shell /bin/bash jarvis
WORKDIR /app

# Copier requirements et installer dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier code source
COPY . .

# Créer dossiers nécessaires
RUN mkdir -p /app/config /app/logs /app/cache && \
    chown -R jarvis:jarvis /app

# Changer vers utilisateur non-root
USER jarvis

# Port d'écoute
EXPOSE 5010

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5010/api/health || exit 1

# Point d'entrée
CMD ["python", "main.py"]