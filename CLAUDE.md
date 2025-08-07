# JARVIS AI Project - Claude Assistant Memory

## 🎯 Project Overview
**JARVIS AI 2025** - Multi-Modal AI Assistant with Microservices Architecture
- Version: 3.0.0
- Architecture: Docker Microservices + FastAPI + React
- Status: 91% Production-Ready

## 🚀 Quick Navigation

### Main Entry Points
- **Start Application**: `python start_jarvis.py` or `docker-compose up -d`
- **Main API**: `services/brain-api/main.py` (port 8080)
- **Frontend**: `ui/src/App.js` (port 3000)
- **Documentation**: `http://localhost:8080/docs`

### Service Locations & Ports
```
brain-api:       services/brain-api/       :8080  (Main API)
tts-service:     services/tts-service/     :5002  (Text-to-Speech)
stt-service:     services/stt-service/     :5003  (Speech-to-Text)
system-control:  services/system-control/  :5004  (System Control)
mcp-gateway:     services/mcp-gateway/     :5006  (MCP Integration)
frontend:        ui/                       :3000  (React Interface)
ollama:          -                         :11434 (LLM)
postgresql:      services/memory-db/       :5432  (Database)
redis:           services/redis/           :6379  (Cache)
```

## 🔍 Smart Search Patterns

### Find API Endpoints
- Routes: `services/brain-api/api/routes/*.py`
- WebSocket: `services/brain-api/core/websocket_manager.py`
- Authentication: Search for `JWT`, `verify_token`, `@router.post`

### Find UI Components
- Main components: `ui/src/components/*.jsx`
- Key files: `JarvisInterface.jsx`, `SituationRoom.jsx`, `VoiceWaveform.jsx`, `Sphere3D.js`
- Styles: `ui/src/styles/*.css`

### Find Configuration
- Docker: `docker-compose*.yml` (10 files)
- Environment: `.env` files (gitignored)
- Settings: `config/settings.py`

### Find Tests
- Backend: `tests/backend/*.py`
- Integration: `tests/integration/*.py`
- Frontend: `tests/frontend/*.js`

## 🛠️ Common Tasks

### Start Services
```bash
# Full stack
docker-compose up -d

# Individual pods
docker-compose -f docker-compose.ai-pod.yml up -d
docker-compose -f docker-compose.audio-pod.yml up -d
```

### Run Tests
```bash
# Backend tests
pytest tests/backend/

# Integration tests
pytest tests/integration/

# Frontend tests
cd ui && npm test
```

### Clean Project
```bash
python cleanup-project.py --execute --force
```

### Check Service Health
```bash
curl http://localhost:8080/health
curl http://localhost:5002/health
curl http://localhost:5003/health
```

## 🔴 Critical Issues to Fix

### Security (CRITICAL)
1. **system-control exposed** on port 5004 without auth
2. **Docker SYS_PTRACE** capability is dangerous
3. **JWT auth incomplete** on sensitive endpoints

### Performance (HIGH)
1. **brain-api/main.py** - 530 lines, needs refactoring
2. **memory_system.py** - 790 lines, too complex
3. **PostgreSQL indexes** missing on key tables
4. **Redis clustering** not configured

### Code Quality (MEDIUM)
1. **TODOs in Brain API** using fake data
2. **Tests at root** need migration to tests/
3. **Bundle size** 2.8MB (target <2MB)

## 📦 Key Dependencies

### Python Core
- FastAPI + Uvicorn (API framework)
- Pydantic (validation)
- SQLAlchemy + pgvector (database)
- Redis (cache)
- Ollama (LLM integration)

### Frontend
- React 18 + Material-UI
- Three.js (3D visualizations)
- Web Audio API (voice)
- WebSocket (real-time)

## 🔧 Development Commands

### Lint & Format
```bash
# Python
black services/ core/ tools/
isort services/ core/ tools/
pylint services/brain-api/

# JavaScript
cd ui && npm run lint
```

### Database Operations
```bash
# Connect to PostgreSQL
docker exec -it jarvis-memory-db psql -U jarvis -d jarvis_memory

# Redis CLI
docker exec -it jarvis-redis redis-cli
```

### Monitoring
```bash
# View logs
docker-compose logs -f brain-api
docker-compose logs -f tts-service

# Metrics
open http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana
```

## 🎯 Optimization Priorities

### Immediate (Week 1)
- [ ] Fix system-control security
- [ ] Complete JWT implementation
- [ ] Refactor brain-api/main.py

### Short-term (Month 1)
- [ ] Add OpenRouter integration
- [ ] Optimize database indexes
- [ ] Implement Redis clustering

### Long-term (Quarter)
- [ ] Migrate to Kubernetes
- [ ] Implement service mesh
- [ ] Multi-tenant architecture

## 🔌 Integration Points

### LLM Services
- **Primary**: Ollama (localhost:11434)
- **Needed**: OpenRouter fallback
- **Models**: llama3.2:3b, deepseek-coder:6.7b, llava:7b

### External APIs Needed
- OpenRouter API for cloud LLM fallback
- Google Drive/Slack MCP servers
- OAuth providers for SSO

## 📝 Project Memory

### File Structure Memory
- **JSON Memory**: `JARVIS_PROJECT_MEMORY.json`
- **MCP Server**: `mcp-tools/jarvis-mcp-server.py`
- **Cleanup Script**: `cleanup-project.py`

### Quick File Counts
- Services: 8 microservices
- Docker Compose: 10 files
- Python files: ~300+
- React components: ~50+
- Tests: ~40+ files

## 🚨 Never Forget

1. **ALWAYS check security** before deploying
2. **Run tests** before committing
3. **Update this file** when structure changes
4. **Use MCP server** for complex searches
5. **Check memory JSON** for detailed structure

## 🤖 Assistant Instructions

When working on JARVIS AI:
1. Check `JARVIS_PROJECT_MEMORY.json` for detailed structure
2. Use `mcp-tools/jarvis-mcp-server.py` for intelligent search
3. Reference service ports from this file
4. Follow security fixes as priority
5. Maintain microservices isolation

## Last Updated
- Date: 2025-08-03
- Cleanup performed: 565MB freed
- Files organized: Tests moved, cache cleared
- Security issues identified: 3 critical, 5 high