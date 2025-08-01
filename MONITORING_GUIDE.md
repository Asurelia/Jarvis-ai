# 🔍 JARVIS AI 2025 - Guide du Système de Monitoring

## Vue d'ensemble

Le système de monitoring JARVIS AI fournit une observabilité complète avec :

- **Prometheus** : Collecte de métriques en temps réel
- **Grafana** : Dashboards et visualisations 
- **Alertmanager** : Gestion intelligente des alertes
- **Loki** : Centralisation des logs
- **Jaeger** : Tracing distribué des requêtes
- **Exporters** : Métriques système, Redis, PostgreSQL

## 🚀 Démarrage Rapide

### Windows
```batch
# Démarrer le monitoring
start-monitoring.bat

# Ou manuellement
docker-compose -f docker-compose.monitoring.yml up -d
```

### Linux/macOS
```bash
# Rendre le script exécutable
chmod +x start-monitoring.sh

# Démarrer le monitoring
./start-monitoring.sh

# Ou manuellement
docker-compose -f docker-compose.monitoring.yml up -d
```

## 📊 Accès aux Services

| Service | URL | Identifiants |
|---------|-----|--------------|
| Grafana | http://localhost:3001 | admin / jarvis2025! |
| Prometheus | http://localhost:9090 | - |
| AlertManager | http://localhost:9093 | - |
| Jaeger | http://localhost:16686 | - |

## 📈 Dashboards Disponibles

### 🤖 JARVIS Overview
- **URL** : http://localhost:3001/d/jarvis-overview
- **Contenu** : Vue d'ensemble de tous les services JARVIS
- **Métriques** : Statut, latence, connexions actives, GPU

### 🧠 AI Services Dashboard
- **URL** : http://localhost:3001/d/jarvis-ai-services
- **Contenu** : Monitoring des services IA (Brain API, TTS, STT)
- **Métriques** : Temps de réponse IA, synthèse TTS, transcription STT

### 🎮 GPU Monitoring  
- **URL** : http://localhost:3001/d/jarvis-gpu
- **Contenu** : Surveillance GPU AMD RX 7800 XT
- **Métriques** : Utilisation, température, mémoire, consommation

### 🏗️ Infrastructure
- **URL** : http://localhost:3001/d/jarvis-infra
- **Contenu** : Métriques système et infrastructure
- **Métriques** : CPU, RAM, disque, réseau, containers

### 🔒 Security Dashboard
- **URL** : http://localhost:3001/d/jarvis-security
- **Contenu** : Monitoring sécurité système
- **Métriques** : Violations, rate limiting, accès non autorisés

## 🚨 Système d'Alertes

### Configuration des Notifications

#### Email (SMTP)
```bash
# Variables d'environnement
export SMTP_HOST="smtp.gmail.com:587"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export TEAM_EMAIL="admin@yourcompany.com"
```

#### Slack
```bash
# Webhook Slack
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

### Types d'Alertes

#### 🔴 Critiques (Notification immédiate)
- Service JARVIS indisponible
- Température GPU > 80°C
- Violations de sécurité
- Mémoire système > 90%

#### 🟡 Avertissements
- Latence IA élevée (> 10s)
- Utilisation GPU > 90%
- Taux d'erreur > 10%
- Espace disque < 15%

#### 📊 Business
- Aucune conversation depuis 30min
- Échecs de synthèse TTS fréquents
- Performance globale dégradée

## 📝 Logs Centralisés

### Requêtes Loki Utiles

#### Logs d'erreur par service
```logql
{job="jarvis-services"} |= "ERROR"
```

#### Logs Brain API avec conversation ID
```logql
{service="brain-api"} | json | conversation_id != ""
```

#### Logs TTS avec temps de synthèse élevé
```logql
{service="tts-service"} | json | synthesis_time > 5
```

#### Violations de sécurité
```logql
{service="system-control"} | json | security_level = "VIOLATION"
```

### Débogage avec les Logs
```bash
# Suivre les logs en temps réel
docker-compose -f docker-compose.monitoring.yml logs -f

# Logs d'un service spécifique
docker-compose -f docker-compose.monitoring.yml logs grafana

# Logs avec timestamps
docker-compose -f docker-compose.monitoring.yml logs -t loki
```

## 🔍 Métriques Custom

### Métriques Business Implémentées

#### Brain API
- `brain_api_conversations_started_total` : Conversations initiées
- `brain_api_ai_response_time_seconds` : Temps de réponse IA
- `brain_api_memory_operations_total` : Opérations mémoire
- `brain_api_websocket_connections_active` : Connexions WebSocket

#### TTS Service
- `tts_synthesis_duration_seconds` : Durée de synthèse
- `tts_audio_generation_duration_seconds` : Durée audio générée
- `tts_streaming_sessions_active` : Sessions streaming actives

#### STT Service  
- `stt_transcription_duration_seconds` : Durée de transcription
- `stt_audio_duration_seconds` : Durée audio traitée
- `stt_websocket_active_connections` : Connexions WebSocket STT

#### GPU Stats
- `gpu_stats_gpu_utilization_percent` : Utilisation GPU
- `gpu_stats_gpu_temperature_celsius` : Température GPU
- `gpu_stats_gpu_memory_usage_bytes` : Mémoire GPU utilisée
- `gpu_stats_gpu_power_draw_watts` : Consommation énergétique

### Ajout de Métriques Custom

```python
from monitoring.prometheus_instrumentation import PrometheusInstrumentation

# Initialiser l'instrumentation
metrics = PrometheusInstrumentation("mon-service")

# Ajouter une métrique custom
custom_metric = metrics.add_custom_metric(
    "counter", 
    "custom_operations_total",
    "Total custom operations",
    ["operation_type"]
)

# Utiliser la métrique
custom_metric.labels(operation_type="important").inc()
```

## 🔄 Tracing Distribué

### Configuration OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configuration du tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
```

### Utilisation du Tracing
```python
@tracer.start_as_current_span("ai_processing")
def process_ai_request(request):
    with tracer.start_as_current_span("model_inference") as span:
        span.set_attribute("model.name", "jarvis-gpt")
        span.set_attribute("request.id", request.id)
        
        # Traitement...
        result = model.process(request)
        
        span.set_attribute("response.tokens", len(result))
        return result
```

## 🛠️ Maintenance et Troubleshooting

### Commandes Utiles

```bash
# Statut des services
docker-compose -f docker-compose.monitoring.yml ps

# Redémarrer un service
docker-compose -f docker-compose.monitoring.yml restart grafana

# Voir l'utilisation des ressources
docker stats

# Nettoyer les volumes (⚠️ Perte de données)
docker-compose -f docker-compose.monitoring.yml down -v
```

### Problèmes Courants

#### Grafana ne démarre pas
```bash
# Vérifier les permissions
chmod -R 755 monitoring/data/grafana/
chown -R 472:472 monitoring/data/grafana/

# Redémarrer
docker-compose -f docker-compose.monitoring.yml restart grafana
```

#### Prometheus ne collecte pas les métriques
```bash
# Vérifier la configuration
docker-compose -f docker-compose.monitoring.yml exec prometheus promtool check config /etc/prometheus/prometheus.yml

# Voir les targets
curl http://localhost:9090/api/v1/targets
```

#### Loki ne reçoit pas de logs
```bash
# Vérifier Promtail
docker-compose -f docker-compose.monitoring.yml logs promtail

# Tester la connectivité
curl -X POST http://localhost:3100/loki/api/v1/push
```

### Sauvegarde et Restauration

#### Sauvegarde des données
```bash
# Créer une sauvegarde
tar -czf jarvis-monitoring-backup-$(date +%Y%m%d).tar.gz monitoring/data/

# Sauvegarde automatique (cron)
0 2 * * * cd /path/to/jarvis && tar -czf backups/monitoring-$(date +\%Y\%m\%d).tar.gz monitoring/data/
```

#### Restauration
```bash
# Arrêter les services
docker-compose -f docker-compose.monitoring.yml down

# Restaurer les données
tar -xzf jarvis-monitoring-backup-20250101.tar.gz

# Redémarrer
docker-compose -f docker-compose.monitoring.yml up -d
```

## 📊 Optimisation des Performances

### Configuration Prometheus
```yaml
# monitoring/config/prometheus.yml
global:
  scrape_interval: 15s          # Collecte toutes les 15s
  evaluation_interval: 15s      # Évaluation des règles

storage:
  tsdb:
    retention.time: 30d         # Rétention 30 jours
    retention.size: 10GB        # Limite de taille
```

### Configuration Grafana
```yaml
# Variables d'environnement pour optimiser
GF_DATABASE_MAX_OPEN_CONNS=300
GF_DATABASE_MAX_IDLE_CONNS=100
GF_ANALYTICS_REPORTING_ENABLED=false
```

### Configuration Loki
```yaml
# monitoring/config/loki.yml
limits_config:
  ingestion_rate_mb: 16         # 16MB/s maximum
  max_query_parallelism: 32     # 32 requêtes parallèles
  retention_period: 168h        # 7 jours
```

## 🔐 Sécurité

### Authentification Grafana
```bash
# Changer le mot de passe admin
export GRAFANA_ADMIN_PASSWORD="votre-mot-de-passe-securise"
```

### Accès Réseau
- Tous les services sont liés à `127.0.0.1` (localhost uniquement)
- Utiliser un reverse proxy (nginx) pour l'accès externe
- Configurer HTTPS avec des certificats SSL

### Chiffrement des Données
```yaml
# Pour une configuration de production
grafana:
  environment:
    - GF_SECURITY_SECRET_KEY=${GRAFANA_SECRET_KEY}
    - GF_DATABASE_SSL_MODE=require
```

## 📚 Ressources Supplémentaires

- [Documentation Prometheus](https://prometheus.io/docs/)
- [Documentation Grafana](https://grafana.com/docs/)
- [Documentation Loki](https://grafana.com/docs/loki/)
- [Documentation Jaeger](https://www.jaegertracing.io/docs/)

## 🆘 Support

En cas de problème :

1. Consultez les logs : `docker-compose -f docker-compose.monitoring.yml logs`
2. Vérifiez la santé des services : `docker-compose -f docker-compose.monitoring.yml ps`
3. Testez la connectivité réseau
4. Consultez cette documentation

---

**🤖 JARVIS AI 2025 - Monitoring System**  
*Système de monitoring production-ready pour une observabilité complète*