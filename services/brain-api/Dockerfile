# 🧠 Brain API Dockerfile - Cerveau central JARVIS
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="JARVIS Team"
LABEL description="Brain API - Métacognition, Agent, Memory Manager"
LABEL version="2.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Créer utilisateur non-root
RUN useradd -m -u 1000 jarvis && \
    mkdir -p /app && \
    chown -R jarvis:jarvis /app

# Répertoire de travail
WORKDIR /app

# Copier et installer dépendances Python
COPY requirements_simple.txt .
RUN pip install --no-cache-dir -r requirements_simple.txt

# Copier le code source
COPY . .
RUN chown -R jarvis:jarvis /app

# Utilisateur non-root
USER jarvis

# Exposer les ports
EXPOSE 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Point d'entrée
CMD ["python", "main.py"]