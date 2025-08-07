FROM python:3.11-slim

LABEL maintainer="JARVIS AI Team"
LABEL service="integration-router"
LABEL version="1.0.0"

# Security: Create non-root user
RUN groupadd -r jarvis && useradd --no-log-init -r -g jarvis jarvis

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R jarvis:jarvis /app

# Switch to non-root user
USER jarvis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5022/health || exit 1

# Expose port
EXPOSE 5022

# Start the application
CMD ["python", "main.py"]