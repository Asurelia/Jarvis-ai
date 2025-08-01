@echo off
REM 🔍 JARVIS AI 2025 - Démarrage du système de monitoring complet
REM Script Windows pour lancer Prometheus, Grafana, Alertmanager, Loki et Jaeger

echo.
echo ===============================================
echo 🤖 JARVIS AI 2025 - Monitoring Stack
echo ===============================================
echo.

REM Vérification Docker
echo ⏳ Vérification de Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker n'est pas installé ou démarré
    echo Veuillez installer Docker Desktop et le démarrer
    pause
    exit /b 1
)
echo ✅ Docker trouvé

REM Vérification docker-compose
echo ⏳ Vérification de Docker Compose...
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose n'est pas disponible
    pause
    exit /b 1
)
echo ✅ Docker Compose trouvé

REM Création des répertoires de données
echo ⏳ Création des répertoires de données...
if not exist "monitoring\data" mkdir "monitoring\data"
if not exist "monitoring\data\prometheus" mkdir "monitoring\data\prometheus"
if not exist "monitoring\data\grafana" mkdir "monitoring\data\grafana"
if not exist "monitoring\data\alertmanager" mkdir "monitoring\data\alertmanager"
if not exist "monitoring\data\loki" mkdir "monitoring\data\loki"
if not exist "monitoring\data\jaeger" mkdir "monitoring\data\jaeger"

REM Permissions pour les volumes (Windows)
echo ⏳ Configuration des permissions...
icacls "monitoring\data" /grant Everyone:(OI)(CI)F /T >nul 2>&1

REM Variables d'environnement par défaut si pas définies
if not defined GRAFANA_ADMIN_PASSWORD set GRAFANA_ADMIN_PASSWORD=jarvis2025!
if not defined REDIS_PASSWORD set REDIS_PASSWORD=jarvis_redis_2025!
if not defined POSTGRES_PASSWORD set POSTGRES_PASSWORD=jarvis_db_2025!

echo.
echo 🚀 Démarrage de la stack de monitoring...
echo.

REM Arrêt des services existants
echo ⏳ Arrêt des services de monitoring existants...
docker-compose -f docker-compose.monitoring.yml down -v 2>nul

REM Démarrage des services de monitoring
echo ⏳ Démarrage des services de monitoring...
docker-compose -f docker-compose.monitoring.yml up -d

if errorlevel 1 (
    echo ❌ Erreur lors du démarrage des services de monitoring
    echo Vérifiez les logs avec: docker-compose -f docker-compose.monitoring.yml logs
    pause
    exit /b 1
)

echo.
echo ⏳ Attente du démarrage des services (30 secondes)...
timeout /t 30 /nobreak >nul

echo.
echo ✅ Stack de monitoring JARVIS démarrée avec succès!
echo.
echo 📊 Accès aux services:
echo    • Grafana:      http://localhost:3001 (admin/jarvis2025!)
echo    • Prometheus:   http://localhost:9090
echo    • AlertManager: http://localhost:9093
echo    • Jaeger:       http://localhost:16686
echo.
echo 📈 Dashboards Grafana disponibles:
echo    • JARVIS Overview: http://localhost:3001/d/jarvis-overview
echo    • AI Services:     http://localhost:3001/d/jarvis-ai-services
echo    • GPU Monitoring:  http://localhost:3001/d/jarvis-gpu  
echo    • Infrastructure:  http://localhost:3001/d/jarvis-infra
echo.
echo 🔍 Pour voir les logs: docker-compose -f docker-compose.monitoring.yml logs -f
echo 🔄 Pour redémarrer:   docker-compose -f docker-compose.monitoring.yml restart
echo 🛑 Pour arrêter:      docker-compose -f docker-compose.monitoring.yml down
echo.

REM Vérification santé des services
echo ⏳ Vérification de la santé des services...
timeout /t 10 /nobreak >nul

echo.
echo Service Status:
docker-compose -f docker-compose.monitoring.yml ps

echo.
echo 🎉 Système de monitoring JARVIS AI prêt!
echo    Consultez Grafana pour visualiser vos métriques
echo.
pause