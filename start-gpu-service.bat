@echo off
echo 🎮 JARVIS AI - Demarrage du service GPU Stats
echo ===============================================

echo.
echo 🚀 Demarrage du service gpu-stats-service...
docker-compose up -d gpu-stats-service

echo.
echo ⏳ Attente du demarrage du service (10 secondes)...
timeout /t 10 /nobreak > nul

echo.
echo 🔍 Verification de l'etat du service...
docker ps --filter "name=jarvis_gpu_stats" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo.
echo 🏥 Test du health check...
curl -s http://localhost:5009/health

echo.
echo.
echo 📊 Test des stats GPU...
curl -s http://localhost:5009/gpu/stats

echo.
echo.
echo 🌐 URLs importantes:
echo    - API: http://localhost:5009  
echo    - Health: http://localhost:5009/health
echo    - Stats: http://localhost:5009/gpu/stats
echo    - WebSocket: ws://localhost:5009/ws/gpu-stats

echo.
echo 🧪 Pour executer les tests d'integration:
echo    python test_gpu_integration.py

echo.
echo ✅ Service GPU Stats demarre!
pause