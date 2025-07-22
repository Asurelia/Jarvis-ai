# 🎭 Dockerfile pour les tests E2E Playwright
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

# Variables d'environnement
ENV NODE_ENV=test
ENV CI=true

# Répertoire de travail
WORKDIR /app

# Copie des fichiers de configuration
COPY package*.json ./
COPY playwright.config.js ./

# Installation des dépendances
RUN npm ci

# Installation des navigateurs Playwright
RUN npx playwright install --with-deps

# Copie des tests
COPY specs/ ./specs/
COPY fixtures/ ./fixtures/ 2>/dev/null || true
COPY utils/ ./utils/ 2>/dev/null || true

# Création des répertoires de résultats
RUN mkdir -p test-results playwright-report screenshots

# Configuration des permissions
RUN chmod -R 755 /app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD npx playwright --version

# Point d'entrée
ENTRYPOINT ["npx", "playwright", "test"]
CMD ["--reporter=html"]