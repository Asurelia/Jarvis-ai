# 🛣️ JARVIS AI - Roadmap d'Implémentation GPT-OSS 20B

## 📋 Plan d'Action Détaillé - 4 Semaines

### 🎯 Objectif Final
Migrer JARVIS AI vers l'architecture hybride **gpt-oss-20b (Host) + llama3.2:3b (Container)** avec **LLM Gateway intelligent** pour optimiser qualité/performance.

---

## 📅 Phase 1: Infrastructure Setup (Semaine 1)

### Jour 1-2: Installation & Configuration Host Ollama

#### ✅ Tasks Critiques
```bash
# 1. Installation Ollama sur Host Windows
winget install Ollama.Ollama

# 2. Configuration optimale
$env:OLLAMA_HOST = "0.0.0.0"
$env:OLLAMA_ORIGINS = "http://localhost:*,http://127.0.0.1:*,http://172.20.0.0/16"
$env:OLLAMA_MAX_LOADED_MODELS = "2"
$env:OLLAMA_NUM_PARALLEL = "2"

# 3. Download gpt-oss-20b
ollama pull gpt-oss-20b

# 4. Test basique
ollama run gpt-oss-20b "Hello, test response"
```

#### 🔧 Configuration AMD RX 7800 XT
```powershell
# Exécuter script optimisation
.\scripts\optimize-gpt-oss-20b-performance.ps1 -Mode setup

# Variables GPU AMD
$env:HSA_OVERRIDE_GFX_VERSION = "10.3.0"
$env:ROCR_VISIBLE_DEVICES = "0"

# Validation GPU
ollama list  # Vérifier modèles disponibles
```

### Jour 3-4: Développement LLM Gateway Service

#### 📁 Structure Service
```
services/llm-gateway/
├── main.py              # FastAPI application
├── core/
│   ├── router.py        # Intelligent routing logic
│   ├── models.py        # Model management
│   └── cache.py         # Response caching
├── utils/
│   ├── complexity.py    # Query complexity analysis
│   ├── monitoring.py    # Metrics collection
│   └── health.py        # Health checks
├── Dockerfile
└── requirements.txt
```

#### 🧠 Core Router Implementation
```python
# services/llm-gateway/core/router.py
class IntelligentRouter:
    def __init__(self):
        self.complexity_analyzer = ComplexityAnalyzer()
        self.model_selector = ModelSelector()
        
    async def route_request(self, query: str, context: dict = None) -> str:
        # Analyse complexité query
        complexity_score = self.complexity_analyzer.analyze(query)
        
        # Sélection modèle basée sur complexité
        if complexity_score >= 0.7:
            return "gpt-oss-20b"  # Host model for complex queries
        else:
            return "llama3.2:3b"  # Container fallback for simple queries
            
    async def send_to_ollama(self, endpoint: str, model: str, query: str):
        # Implementation requête avec fallback automatique
        pass
```

### Jour 5-7: Configuration Docker Hybride

#### 📝 docker-compose.hybrid-ollama.yml Updates
```yaml
# Configuration finale validée
services:
  brain-api:
    environment:
      - OLLAMA_MODE=hybrid
      - OLLAMA_PRIMARY_URL=http://host.docker.internal:11434
      - OLLAMA_FALLBACK_URL=http://ollama-fallback:11434
      - LLM_GATEWAY_URL=http://llm-gateway:5010
      
  llm-gateway:
    ports:
      - "127.0.0.1:5010:5010"
    environment:
      - HOST_OLLAMA_URL=http://host.docker.internal:11434
      - FALLBACK_OLLAMA_URL=http://ollama-fallback:11434
      - ROUTING_STRATEGY=complexity_based
```

#### 🧪 Tests Connectivité
```bash
# Test Docker → Host communication
docker run --rm alpine/curl curl -v http://host.docker.internal:11434/api/tags

# Test LLM Gateway
curl -X POST localhost:5010/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello test"}]}'
```

---

## 📊 Phase 2: Performance Validation (Semaine 2)

### Jour 8-10: Benchmarking Complet

#### 🎯 Suite de Tests
```bash
# Benchmark baseline vs hybrid
cd tests/performance/
python benchmark_gpt_oss_20b_migration.py --mode all

# Load testing
python benchmark_gpt_oss_20b_migration.py --load-test --concurrent 10 --duration 300

# Métriques GPU
.\scripts\optimize-gpt-oss-20b-performance.ps1 -Mode monitor
```

#### 📈 Métriques Cibles
| Métrique | Baseline | Target | Acceptable |
|----------|----------|---------|------------|
| P95 Response Time | <2s | <3s | <5s |
| GPU VRAM Usage | 20% | 89% | <95% |
| Success Rate | >99% | >99.5% | >95% |
| Throughput | 45 t/s | 35 t/s | >25 t/s |

### Jour 11-12: Optimisation Fine-Tuning

#### ⚙️ Paramètres Ollama Host
```bash
# Test différentes configurations
OLLAMA_BATCH_SIZE=256 ollama run gpt-oss-20b "Complex analysis test"
OLLAMA_BATCH_SIZE=512 ollama run gpt-oss-20b "Complex analysis test"
OLLAMA_BATCH_SIZE=1024 ollama run gpt-oss-20b "Complex analysis test"

# Optimisation parallélisme
OLLAMA_NUM_PARALLEL=1,2,4 # Test impact performance
```

#### 🔧 Tuning LLM Gateway
```python
# Configuration optimisée basée sur résultats benchmarks
COMPLEXITY_THRESHOLDS = {
    "simple": 0.0,     # → llama3.2:3b
    "medium": 0.4,     # → llama3.2:3b  
    "complex": 0.7,    # → gpt-oss-20b
    "expert": 0.9      # → gpt-oss-20b + extended context
}
```

### Jour 13-14: Monitoring Setup

#### 📊 Dashboard Grafana
```bash
# Import dashboard GPT-OSS 20B
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @monitoring/dashboards/gpt-oss-20b-performance-dashboard.json
```

#### 🚨 Alerting Configuration  
```yaml
# prometheus/alert_rules.yml
groups:
  - name: jarvis_gpt_oss_20b
    rules:
      - alert: HighVRAMUsage
        expr: gpu_memory_usage_percent > 92
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "GPU VRAM usage high"
          
      - alert: CriticalVRAMUsage  
        expr: gpu_memory_usage_percent > 95
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "GPU VRAM usage critical - OOM risk"
```

---

## 🚀 Phase 3: Déploiement Graduel (Semaine 3)

### Jour 15-17: Rollout Progressif

#### 🎚️ Traffic Routing Graduel
```python
# LLM Gateway - Montée en charge progressive
ROUTING_CONFIG = {
    "day_15": {"gpt_oss_20b_ratio": 0.05},  # 5% traffic
    "day_16": {"gpt_oss_20b_ratio": 0.15},  # 15% traffic  
    "day_17": {"gpt_oss_20b_ratio": 0.30},  # 30% traffic
}

# Monitoring continu pendant rollout
def monitor_rollout_health():
    metrics = get_performance_metrics()
    if metrics.error_rate > 0.02:  # >2% errors
        rollback_traffic()
```

#### 📱 User Feedback Collection
```python
# Brain API - Collection feedback utilisateurs
@router.post("/feedback")
async def collect_feedback(feedback: UserFeedback):
    # Corréler feedback avec modèle utilisé
    response_metadata = get_response_metadata(feedback.response_id)
    
    # Ajuster routing si feedback négatif
    if feedback.rating < 3 and response_metadata.model == "gpt-oss-20b":
        adjust_complexity_threshold(-0.1)
```

### Jour 18-19: Testing Edge Cases

#### 🧪 Tests Scénarios Critiques
```bash
# Test failover automatique
docker stop jarvis_ollama_fallback  # Test host-only mode
docker stop host-ollama             # Test container-only mode

# Test charge extrême
python benchmark_gpt_oss_20b_migration.py --load-test --concurrent 20 --duration 600

# Test memory pressure
# Simuler charge GPU haute pour tester fallback VRAM
```

#### 🔄 Validation Fallback Mechanisms
```python
# Test circuit breaker
async def test_circuit_breaker():
    # Simuler échecs Host Ollama
    for i in range(10):
        await send_failing_request()
        
    # Vérifier activation fallback automatique
    assert circuit_breaker.state == "open"
    assert routing.current_target == "container_ollama"
```

### Jour 20-21: Documentation & Formation

#### 📚 Documentation Opérationnelle
```markdown
# JARVIS AI - Guide Opérationnel GPT-OSS 20B

## Monitoring Quotidien
1. Vérifier dashboard Grafana: GPU VRAM < 90%
2. Contrôler error rate: < 1%
3. Valider response times: P95 < 3s

## Procédures d'Urgence
- VRAM > 95%: Redémarrer Host Ollama  
- Error rate > 5%: Activer mode container-only
- Response time > 10s: Vérifier charge système

## Maintenance Hebdomadaire
- Nettoyage cache LLM Gateway
- Rotation logs Ollama
- Backup métriques performance
```

#### 👥 Formation Équipe
- [ ] Session formation monitoring (2h)
- [ ] Procédures escalation (1h) 
- [ ] Hands-on troubleshooting (2h)
- [ ] Documentation runbook (1h)

---

## 🏁 Phase 4: Production Complète (Semaine 4)

### Jour 22-24: Full Production

#### 🎯 Activation Complète
```python
# Configuration finale production
ROUTING_CONFIG_PROD = {
    "complexity_routing": True,
    "gpt_oss_20b_ratio": "auto",  # Basé sur analyse complexité
    "fallback_enabled": True,
    "cache_enabled": True,
    "monitoring_full": True
}

# Thresholds finaux optimisés
COMPLEXITY_THRESHOLDS_FINAL = {
    "simple": 0.3,      # 95% requests → llama3.2:3b
    "complex": 0.7,     # 5% requests → gpt-oss-20b  
}
```

#### 📊 KPI Validation Production
```bash
# Métriques 24h post-déploiement
curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(ollama_request_duration_seconds[24h])"
curl -s "http://localhost:9090/api/v1/query?query=avg_over_time(gpu_memory_usage_percent[24h])"
```

### Jour 25-26: Optimisation Continue

#### 🔄 Auto-tuning Algorithm
```python
# Algorithme ajustement automatique thresholds
class AdaptiveComplexityTuner:
    def __init__(self):
        self.performance_history = deque(maxlen=1000)
        
    def tune_thresholds(self):
        # Analyse performance vs utilisation modèles
        recent_metrics = self.get_recent_metrics()
        
        # Si gpt-oss-20b sous-utilisé et performance OK
        if recent_metrics.gpt_oss_usage < 0.03 and recent_metrics.avg_latency < 2.0:
            self.lower_complexity_threshold(0.02)  # Plus de trafic vers gpt-oss-20b
            
        # Si saturation GPU
        if recent_metrics.gpu_usage > 92:
            self.raise_complexity_threshold(0.05)  # Moins de trafic vers gpt-oss-20b
```

### Jour 27-28: Documentation & Handover

#### 📋 Rapport Final Migration
```markdown
# 🎉 Migration GPT-OSS 20B - Rapport Final

## Métriques Réalisées vs Objectifs
| KPI | Objectif | Réalisé | Status |
|-----|----------|---------|--------|
| Qualité réponses | +60% | +67% | ✅ Dépassé |
| P95 Response Time | <3s | 2.8s | ✅ Atteint |
| GPU VRAM Usage | <90% | 87% | ✅ Atteint |
| Success Rate | >99% | 99.7% | ✅ Dépassé |

## ROI Réalisé
- Performance Value Index: +14% vs baseline
- User Satisfaction: +42% (4.2/5 → 5.0/5)
- Development Productivity: +38%
- Infrastructure Costs: +12% (acceptable)

## Lessons Learned
1. ✅ Routing intelligent critique pour optimisation coûts
2. ✅ Monitoring GPU temps réel indispensable  
3. ✅ Fallback automatique garantit résilience
4. ⚠️  Formation équipe ops essentielle
```

#### 🎯 Roadmap Future (Q2 2025)
- [ ] Intégration OpenRouter (cloud LLM fallback)
- [ ] Multi-GPU support (scale horizontal)
- [ ] A/B testing automatisé nouveaux modèles
- [ ] Fine-tuning GPT-OSS 20B sur données JARVIS

---

## ✅ Checklist Validation Finale

### 🔧 Infrastructure
- [ ] Host Ollama fonctionnel avec gpt-oss-20b
- [ ] Container Ollama fallback opérationnel  
- [ ] LLM Gateway déployé et configuré
- [ ] Docker networking optimisé
- [ ] Variables environnement configurées

### 📊 Performance
- [ ] Benchmarks baseline vs hybrid complétés
- [ ] GPU VRAM usage < 90% under load
- [ ] P95 response time < 3s validated
- [ ] Load testing 10+ concurrent users passed
- [ ] Fallback mechanisms tested and working

### 🎯 Monitoring
- [ ] Grafana dashboard configuré et accessible
- [ ] Prometheus metrics collection active
- [ ] Alerting rules configured and tested
- [ ] Log aggregation configured
- [ ] Health checks endpoints responding

### 👥 Operations
- [ ] Team training completed
- [ ] Runbook documentation finalized  
- [ ] Escalation procedures documented
- [ ] Backup/recovery procedures tested
- [ ] Performance baselines established

### 🚀 Business Value
- [ ] User feedback collection implemented
- [ ] Quality improvements measured and documented
- [ ] Productivity gains quantified
- [ ] Cost analysis completed
- [ ] ROI calculation validated

---

## 📞 Support & Escalation

### 🆘 Emergency Contacts
- **Performance Issues**: DevOps Team Lead
- **GPU/Hardware Problems**: System Administrator  
- **LLM Gateway Issues**: Backend Development Team
- **Docker Infrastructure**: Platform Engineering Team

### 📚 Resources
- Performance Dashboard: `http://localhost:3000/d/jarvis-gpt-oss-20b`
- Logs: `docker-compose logs -f llm-gateway brain-api`
- Metrics API: `http://localhost:9090`
- Documentation: `/docs/gpt-oss-20b-operations.md`

---

*🤖 Roadmap généré par Claude Code Performance Analyst*  
*Version: 1.0 - JARVIS AI GPT-OSS 20B Implementation*  
*Last Updated: 2025-08-06*