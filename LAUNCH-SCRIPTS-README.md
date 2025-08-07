# 🚀 JARVIS AI - Launch Scripts Guide

## 📋 Available Scripts

### 🎯 **JARVIS-LAUNCH-ALL.bat** - Complete First-Time Setup
**When to use**: First installation or complete system setup

**Features**:
- ✅ Checks all prerequisites (Python, Docker, Node.js)
- ✅ Creates virtual environment and installs dependencies
- ✅ Generates secure environment variables
- ✅ Builds all Docker images
- ✅ Starts all services in correct order
- ✅ Runs comprehensive health checks
- ✅ Opens browser automatically
- ✅ Provides monitoring loop

**Usage**:
```bash
# Right-click and "Run as administrator"
JARVIS-LAUNCH-ALL.bat
```

**Time**: 5-15 minutes (depending on internet and hardware)

---

### ⚡ **JARVIS-QUICK-START.bat** - Fast Daily Startup
**When to use**: Daily development when everything is already configured

**Features**:
- ✅ Fast startup (assumes environment is ready)
- ✅ Starts only core services
- ✅ Basic health check
- ✅ Opens browser

**Usage**:
```bash
JARVIS-QUICK-START.bat
```

**Time**: 30-60 seconds

---

### 📊 **JARVIS-STATUS.bat** - Real-Time Monitoring
**When to use**: Monitor running services, debug issues

**Features**:
- ✅ Real-time service status
- ✅ Health checks for all endpoints  
- ✅ Resource usage monitoring
- ✅ Port usage analysis
- ✅ Interactive log viewing
- ✅ Service restart options

**Usage**:
```bash
JARVIS-STATUS.bat
```

**Interactive Menu**:
- `R` - Refresh status
- `L` - View service logs
- `S` - Start/restart services
- `Q` - Quit monitor

---

### 🛑 **JARVIS-STOP-ALL.bat** - Complete Shutdown
**When to use**: Stop all JARVIS services and clean up

**Features**:
- ✅ Stops all Docker containers
- ✅ Kills Node.js and Python processes
- ✅ Cleans Docker resources
- ✅ Checks for persistent processes
- ✅ Complete resource cleanup

**Usage**:
```bash
JARVIS-STOP-ALL.bat
```

---

### 💻 **JARVIS-LAUNCH-ALL.ps1** - PowerShell Advanced Launcher
**When to use**: Advanced users preferring PowerShell with logging

**Features**:
- ✅ Advanced error handling
- ✅ Detailed logging to file
- ✅ Parameter support
- ✅ Better status reporting
- ✅ Parallel operations

**Usage**:
```powershell
# Basic usage
.\JARVIS-LAUNCH-ALL.ps1

# With parameters
.\JARVIS-LAUNCH-ALL.ps1 -DevMode -LogFile "my-launch.log"
.\JARVIS-LAUNCH-ALL.ps1 -SkipChecks -Quiet
```

**Parameters**:
- `-SkipChecks` - Skip prerequisite checks
- `-DevMode` - Developer mode (ignore port conflicts)
- `-Quiet` - Suppress console output
- `-LogFile` - Custom log file path

---

## 🔧 Troubleshooting Guide

### ❌ Common Issues

#### **Docker Not Running**
```
[ERROR] Docker is not running!
```
**Solution**: Start Docker Desktop manually or use full launcher

#### **Ports Already in Use**
```
[WARNING] Port 8080 is already in use
```
**Solution**: 
1. Use `JARVIS-STOP-ALL.bat` first
2. Or kill specific processes: `taskkill /F /IM node.exe`

#### **Permission Denied**
```
Access is denied
```
**Solution**: Run as Administrator (Right-click → "Run as administrator")

#### **Python Not Found**
```
'python' is not recognized
```
**Solution**: Install Python 3.11+ and add to PATH

#### **Build Failures**
```
Docker build failed
```
**Solution**:
1. Ensure Docker has enough memory (4GB+)
2. Clear Docker cache: `docker system prune -a`
3. Check internet connection

---

## 📈 Performance Tips

### 🚀 **Optimize Startup Time**

1. **Use SSD**: Store project on SSD for faster Docker builds
2. **Increase Docker Memory**: Set Docker Desktop to 6-8GB RAM
3. **Close Unnecessary Apps**: Free up system resources
4. **Use Quick Start**: After initial setup, use `JARVIS-QUICK-START.bat`

### 🔍 **Monitor Resources**

```bash
# Check Docker resource usage
docker stats

# Check Windows processes
tasklist | findstr python
tasklist | findstr node

# Check port usage
netstat -an | findstr :8080
```

---

## 🎯 Usage Scenarios

### 🏠 **First Time Setup (New Machine)**
```bash
1. JARVIS-LAUNCH-ALL.bat (as Administrator)
2. Wait for complete setup (5-15 minutes)
3. Verify at http://localhost:3000
```

### 💼 **Daily Development Workflow**
```bash
1. JARVIS-QUICK-START.bat (morning startup)
2. JARVIS-STATUS.bat (monitoring during development)
3. JARVIS-STOP-ALL.bat (end of day cleanup)
```

### 🐛 **Debugging Issues**
```bash
1. JARVIS-STATUS.bat (check what's running)
2. Use 'L' option to view specific service logs
3. Use 'S' option to restart problematic services
```

### 🧹 **Clean Environment Reset**
```bash
1. JARVIS-STOP-ALL.bat (complete shutdown)
2. python cleanup-project.py --execute --force (clean files)
3. JARVIS-LAUNCH-ALL.bat (fresh start)
```

---

## 🔐 Security Notes

### ⚠️ **Administrator Privileges**
- Required for Docker operations and service management
- Only `JARVIS-LAUNCH-ALL.bat` requires admin privileges
- Other scripts can run as regular user

### 🔒 **Generated Secrets**
- Scripts automatically generate secure passwords
- Environment variables stored in `.env` (gitignored)
- JWT tokens rotated on each launch

### 🛡️ **Safe Practices**
- Never commit `.env` files
- Regularly update Docker images
- Monitor exposed ports with `JARVIS-STATUS.bat`

---

## 🆘 Emergency Commands

### 🚨 **Kill Everything Immediately**
```bash
# Windows Command Prompt
taskkill /F /IM docker.exe
taskkill /F /IM python.exe  
taskkill /F /IM node.exe
docker system prune -a -f
```

### 🔧 **Reset Docker Completely**
```bash
# In Docker Desktop: Settings → Troubleshoot → Reset to factory defaults
# Or via command line:
docker system prune -a --volumes -f
docker network prune -f
```

### 🗂️ **Clean Project Files**
```bash
python cleanup-project.py --execute --force
rmdir /s /q venv
rmdir /s /q ui\node_modules
del .env
```

---

## 📚 Additional Resources

### 🔗 **Quick Links**
- Main Interface: http://localhost:3000
- API Documentation: http://localhost:8080/docs
- Health Check: http://localhost:8080/health
- Voice Bridge: http://localhost:3001

### 📄 **Related Files**
- `CLAUDE.md` - Claude Assistant memory
- `JARVIS_PROJECT_MEMORY.json` - Project structure
- `cleanup-project.py` - File cleanup utility
- `docker-compose*.yml` - Service configurations

### 🆘 **Support**
1. Check `JARVIS-STATUS.bat` for service status
2. Review log files in project root
3. Check Docker Desktop logs
4. Consult `CLAUDE.md` for project navigation

---

## 🎉 Success Indicators

When JARVIS is running correctly, you should see:

✅ **All services healthy** in status monitor  
✅ **Main interface** loads at http://localhost:3000  
✅ **API documentation** available at http://localhost:8080/docs  
✅ **Voice interface** (optional) at http://localhost:3001  
✅ **No error messages** in service logs  
✅ **Resource usage** under control in `docker stats`

---

*Scripts created for JARVIS AI 2025 - The ultimate AI assistant launch system*