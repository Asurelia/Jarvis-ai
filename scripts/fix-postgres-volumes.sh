#!/bin/bash
echo "======================================"
echo "JARVIS AI - PostgreSQL Volume Fix"
echo "======================================"
echo

echo "[INFO] Stopping all services..."
docker-compose down -v

echo "[INFO] Removing PostgreSQL container and volumes..."
docker container rm -f jarvis_memory_db 2>/dev/null || true
docker volume rm jarvis-ai_postgres_data 2>/dev/null || true

echo "[INFO] Cleaning up old PostgreSQL data directory..."
if [ -d "data/postgres" ]; then
    rm -rf "data/postgres"
    echo "[INFO] Removed old postgres data directory"
fi

echo "[INFO] Creating fresh data directories..."
mkdir -p "data/postgres"

echo "[INFO] Starting PostgreSQL with named volume..."
docker-compose up -d memory-db

echo "[INFO] Waiting for PostgreSQL to initialize..."
sleep 30

echo "[INFO] Checking PostgreSQL status..."
docker-compose logs memory-db

echo
echo "[SUCCESS] PostgreSQL volume fix completed!"
echo "The database is now using a named Docker volume for Linux/macOS compatibility."
echo