FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for terminal operations
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    git \
    nano \
    vim \
    htop \
    tree \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create necessary directories
RUN mkdir -p /app/logs /app/cache

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV MAX_TERMINAL_SESSIONS=10
ENV SESSION_TIMEOUT_MINUTES=30

# Create non-root user for security
RUN useradd -m -u 1000 jarvis && \
    chown -R jarvis:jarvis /app
USER jarvis

# Expose port
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5005/health || exit 1

# Start command
CMD ["python", "main.py"]