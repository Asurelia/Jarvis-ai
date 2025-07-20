FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système pour audio et Whisper
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    libsndfile1 \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier code
COPY . .

# Port d'exposition
EXPOSE 5003

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5003/health || exit 1

# Commande de démarrage
CMD ["python", "main.py"]