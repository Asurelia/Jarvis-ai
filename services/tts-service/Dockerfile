# 🗣️ TTS Service - Coqui.ai XTTS Streaming
FROM python:3.11-slim

# Installation des dépendances système pour audio
RUN apt-get update && apt-get install -y \
    git \
    ffmpeg \
    libsndfile1 \
    portaudio19-dev \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer utilisateur non-root
RUN useradd -m -u 1000 jarvis && \
    mkdir -p /app/models /app/cache && \
    chown -R jarvis:jarvis /app

WORKDIR /app

# Copier requirements
COPY requirements_simple.txt requirements.txt ./

# Installer d'abord les dépendances de base
RUN pip install --no-cache-dir -r requirements_simple.txt

# Installer PyTorch et TTS séparément (gros packages)
RUN pip install --no-cache-dir torch==2.1.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir TTS==0.22.0 librosa==0.10.1

# Copier code source
COPY . .

# Permissions
RUN chown -R jarvis:jarvis /app

# Utilisateur non-root
USER jarvis

# Exposer port
EXPOSE 5002

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5002/health || exit 1

# Commande de démarrage
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5002"]