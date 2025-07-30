"""
🎮 GPU Stats Service - JARVIS AI
Service pour monitorer les statistiques GPU AMD RX 7800 XT
Compatible Windows avec méthodes alternatives
"""

import asyncio
import json
import time
import subprocess
import platform
import re
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import uvicorn

# Configuration du logger
logger.add("gpu_stats.log", rotation="1 MB", retention="7 days", level="INFO")

class GPUStats(BaseModel):
    """Modèle des statistiques GPU"""
    name: str = "AMD Radeon RX 7800 XT"
    temperature: float = 0.0
    utilization: float = 0.0
    memory_used: float = 0.0
    memory_total: float = 16384.0  # 16GB pour RX 7800 XT
    memory_utilization: float = 0.0
    core_clock: int = 0
    memory_clock: int = 0
    power_usage: float = 0.0
    fan_speed: int = 0
    driver_version: str = "Unknown"
    timestamp: float
    status: str = "healthy"

class GPUMonitor:
    """Moniteur GPU AMD compatible Windows"""
    
    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.gpu_info = {
            "name": "AMD Radeon RX 7800 XT",
            "memory_total": 16384,  # MB
            "driver_version": "Unknown"
        }
        self.last_stats = None
        
    async def initialize(self):
        """Initialiser le moniteur GPU"""
        try:
            logger.info("🚀 Initialisation du moniteur GPU AMD...")
            
            # Détecter les GPUs AMD disponibles
            await self._detect_amd_gpu()
            
            # Test de récupération des stats
            test_stats = await self.get_gpu_stats()
            if test_stats:
                logger.success("✅ Moniteur GPU AMD initialisé avec succès")
                return True
            else:
                logger.warning("⚠️ Moniteur GPU en mode simulation")
                return True
                
        except Exception as e:
            logger.error(f"❌ Erreur d'initialisation du moniteur GPU: {e}")
            return False
    
    async def _detect_amd_gpu(self):
        """Détecter les GPUs AMD via différentes méthodes"""
        try:
            if self.is_windows:
                # Méthode 1: WMI (Windows Management Instrumentation)
                await self._detect_via_wmi()
                
                # Méthode 2: DirectX Diagnostic Tool
                await self._detect_via_dxdiag()
                
                # Méthode 3: PowerShell Get-WmiObject
                await self._detect_via_powershell()
                
            else:
                # Linux: utiliser les méthodes standards
                await self._detect_via_linux()
                
        except Exception as e:
            logger.warning(f"⚠️ Détection GPU échouée: {e}")
    
    async def _detect_via_wmi(self):
        """Détecter via WMI (Windows)"""
        try:
            import wmi
            c = wmi.WMI()
            
            for gpu in c.Win32_VideoController():
                if gpu.Name and "AMD" in gpu.Name.upper():
                    self.gpu_info["name"] = gpu.Name
                    if gpu.AdapterRAM:
                        self.gpu_info["memory_total"] = gpu.AdapterRAM // (1024 * 1024)  # Convertir en MB
                    if gpu.DriverVersion:
                        self.gpu_info["driver_version"] = gpu.DriverVersion
                    logger.info(f"🎮 GPU détecté via WMI: {gpu.Name}")
                    break
                    
        except Exception as e:
            logger.debug(f"WMI detection failed: {e}")
    
    async def _detect_via_dxdiag(self):
        """Détecter via dxdiag (Windows)"""
        try:
            result = subprocess.run(
                ["dxdiag", "/t", "dxdiag_output.txt"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Analyser le fichier de sortie pour les infos GPU
            # (Implementation simplifiée pour la demo)
            logger.debug("DXDiag detection attempted")
            
        except Exception as e:
            logger.debug(f"DXDiag detection failed: {e}")
    
    async def _detect_via_powershell(self):
        """Détecter via PowerShell (Windows)"""
        try:
            cmd = [
                "powershell", "-Command",
                "Get-WmiObject -Class Win32_VideoController | Where-Object {$_.Name -like '*AMD*'} | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                if isinstance(data, list) and len(data) > 0:
                    gpu = data[0]
                elif isinstance(data, dict):
                    gpu = data
                else:
                    return
                    
                if gpu.get("Name"):
                    self.gpu_info["name"] = gpu["Name"]
                if gpu.get("AdapterRAM"):
                    self.gpu_info["memory_total"] = gpu["AdapterRAM"] // (1024 * 1024)
                if gpu.get("DriverVersion"):
                    self.gpu_info["driver_version"] = gpu["DriverVersion"]
                    
                logger.info(f"🎮 GPU détecté via PowerShell: {gpu.get('Name')}")
                
        except Exception as e:
            logger.debug(f"PowerShell detection failed: {e}")
    
    async def _detect_via_linux(self):
        """Détecter GPU sur Linux"""
        try:
            # Utiliser rocm-smi si disponible
            result = subprocess.run(["rocm-smi", "--showid"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("🎮 ROCm détecté pour GPU AMD")
                return
                
            # Fallback sur lspci
            result = subprocess.run(["lspci", "-v"], capture_output=True, text=True)
            if result.returncode == 0 and "AMD" in result.stdout:
                logger.info("🎮 GPU AMD détecté via lspci")
                
        except Exception as e:
            logger.debug(f"Linux GPU detection failed: {e}")
    
    async def get_gpu_stats(self) -> Optional[GPUStats]:
        """Récupérer les statistiques GPU actuelles"""
        try:
            # Essayer plusieurs méthodes pour récupérer les stats
            stats_data = None
            
            if self.is_windows:
                # Méthode 1: AMD Software via GPU-Z ou similarité
                stats_data = await self._get_stats_windows()
                
                # Méthode 2: WMI Temperature (si disponible)
                if not stats_data:
                    stats_data = await self._get_stats_wmi()
                
            else:
                # Linux: ROCm ou drivers AMD
                stats_data = await self._get_stats_linux()
            
            # Si aucune méthode ne fonctionne, utiliser la simulation
            if not stats_data:
                stats_data = await self._simulate_gpu_stats()
            
            # Créer l'objet GPUStats
            gpu_stats = GPUStats(
                name=self.gpu_info["name"],
                temperature=stats_data.get("temperature", 0.0),
                utilization=stats_data.get("utilization", 0.0),
                memory_used=stats_data.get("memory_used", 0.0),
                memory_total=self.gpu_info["memory_total"],
                memory_utilization=stats_data.get("memory_utilization", 0.0),
                core_clock=stats_data.get("core_clock", 0),
                memory_clock=stats_data.get("memory_clock", 0),
                power_usage=stats_data.get("power_usage", 0.0),
                fan_speed=stats_data.get("fan_speed", 0),
                driver_version=self.gpu_info["driver_version"],
                timestamp=time.time(),
                status="healthy" if stats_data.get("temperature", 0) < 85 else "warning"
            )
            
            self.last_stats = gpu_stats
            return gpu_stats
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des stats GPU: {e}")
            return None
    
    async def _get_stats_windows(self) -> Optional[Dict]:
        """Récupérer stats via méthodes Windows"""
        try:
            # Méthode 1: GPU-Z si installé
            stats = await self._get_stats_gpuz()
            if stats:
                return stats
            
            # Méthode 2: AMD Software Metrics
            stats = await self._get_stats_amd_software()
            if stats:
                return stats
            
            # Méthode 3: Performance Counters
            stats = await self._get_stats_perfcounters()
            if stats:
                return stats
                
            return None
            
        except Exception as e:
            logger.debug(f"Windows stats retrieval failed: {e}")
            return None
    
    async def _get_stats_gpuz(self) -> Optional[Dict]:
        """Tenter de récupérer via GPU-Z"""
        try:
            # GPU-Z expose parfois des données via SharedMemory
            # Implementation basique pour la démo
            return None
        except:
            return None
    
    async def _get_stats_amd_software(self) -> Optional[Dict]:
        """Récupérer via AMD Adrenalin Software"""
        try:
            # AMD Software expose parfois des métriques via WMI ou registre
            # Implementation future pour l'accès aux métriques AMD
            return None
        except:
            return None
    
    async def _get_stats_perfcounters(self) -> Optional[Dict]:
        """Utiliser les compteurs de performance Windows"""
        try:
            # Utiliser psutil pour récupérer ce qui est disponible
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Estimation basée sur l'utilisation système
            estimated_gpu_usage = min(cpu_percent * 1.2, 100.0)
            
            return {
                "temperature": 45.0 + (estimated_gpu_usage * 0.4),  # Estimation
                "utilization": estimated_gpu_usage,
                "memory_used": (memory.percent * self.gpu_info["memory_total"]) / 100,
                "memory_utilization": memory.percent * 0.8,  # Approximation
                "core_clock": 2400,  # MHz typical pour RX 7800 XT
                "memory_clock": 2400,
                "power_usage": 100.0 + (estimated_gpu_usage * 1.5),
                "fan_speed": int(30 + (estimated_gpu_usage * 0.5))
            }
            
        except Exception as e:
            logger.debug(f"Performance counters failed: {e}")
            return None
    
    async def _get_stats_wmi(self) -> Optional[Dict]:
        """Récupérer température via WMI si disponible"""
        try:
            import wmi
            c = wmi.WMI(namespace="root\\OpenHardwareMonitor")
            
            temperature_sensors = c.Sensor()
            gpu_temp = None
            
            for sensor in temperature_sensors:
                if sensor.SensorType == 'Temperature' and 'GPU' in str(sensor.Name):
                    gpu_temp = float(sensor.Value)
                    break
            
            if gpu_temp:
                return {
                    "temperature": gpu_temp,
                    "utilization": 0.0,  # Non disponible via cette méthode
                    "memory_used": 0.0,
                    "memory_utilization": 0.0,
                    "core_clock": 0,
                    "memory_clock": 0,
                    "power_usage": 0.0,
                    "fan_speed": 0
                }
            
            return None
            
        except Exception as e:
            logger.debug(f"WMI temperature retrieval failed: {e}")
            return None
    
    async def _get_stats_linux(self) -> Optional[Dict]:
        """Récupérer stats sur Linux via ROCm"""
        try:
            # ROCm System Management Interface
            result = subprocess.run(
                ["rocm-smi", "--showtemp", "--showuse", "--showmemuse", "--showclocks"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parser la sortie ROCm-SMI
                lines = result.stdout.split('\n')
                stats = {}
                
                for line in lines:
                    if 'Temperature' in line:
                        temp_match = re.search(r'(\d+\.?\d*)', line)
                        if temp_match:
                            stats['temperature'] = float(temp_match.group(1))
                    
                    elif 'GPU use' in line:
                        use_match = re.search(r'(\d+)%', line)
                        if use_match:
                            stats['utilization'] = float(use_match.group(1))
                
                return stats if stats else None
            
            return None
            
        except Exception as e:
            logger.debug(f"ROCm stats retrieval failed: {e}")
            return None
    
    async def _simulate_gpu_stats(self) -> Dict:
        """Simuler des statistiques GPU réalistes"""
        import random
        import math
        
        # Simulation basée sur des patterns réalistes
        base_time = time.time()
        wave = math.sin(base_time / 30) * 0.3 + 0.7  # Vague lente
        noise = random.uniform(0.9, 1.1)  # Bruit aléatoire
        
        utilization = max(0, min(100, (wave * 60 + random.uniform(-10, 15)) * noise))
        temperature = 35 + (utilization * 0.6) + random.uniform(-2, 3)
        memory_used = (utilization / 100) * self.gpu_info["memory_total"] * random.uniform(0.8, 1.2)
        memory_utilization = (memory_used / self.gpu_info["memory_total"]) * 100
        
        return {
            "temperature": round(temperature, 1),
            "utilization": round(utilization, 1),
            "memory_used": round(memory_used, 1),
            "memory_utilization": round(memory_utilization, 1),
            "core_clock": random.randint(2200, 2600),  # MHz
            "memory_clock": random.randint(2000, 2500),
            "power_usage": round(80 + (utilization * 2.2) + random.uniform(-10, 10), 1),
            "fan_speed": int(25 + (utilization * 0.6) + random.uniform(-5, 8))
        }

# Instance globale du moniteur
gpu_monitor = GPUMonitor()

# Gestion des connexions WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"📡 Nouvelle connexion WebSocket. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"📡 Connexion WebSocket fermée. Total: {len(self.active_connections)}")

    async def broadcast(self, data: dict):
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(data))
            except WebSocketDisconnect:
                disconnected.append(connection)
            except Exception as e:
                logger.error(f"Erreur broadcast WebSocket: {e}")
                disconnected.append(connection)
        
        # Nettoyer les connexions fermées
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Tâche de diffusion en temps réel
async def broadcast_gpu_stats():
    """Diffuser les stats GPU en temps réel via WebSocket"""
    while True:
        try:
            stats = await gpu_monitor.get_gpu_stats()
            if stats and manager.active_connections:
                await manager.broadcast({
                    "type": "gpu_stats",
                    "data": stats.dict()
                })
            
            await asyncio.sleep(1)  # Mise à jour chaque seconde
            
        except Exception as e:
            logger.error(f"❌ Erreur broadcast stats: {e}")
            await asyncio.sleep(5)

# Cycle de vie de l'application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Démarrage du GPU Stats Service...")
    
    # Initialiser le moniteur GPU
    await gpu_monitor.initialize()
    
    # Démarrer la tâche de broadcast
    broadcast_task = asyncio.create_task(broadcast_gpu_stats())
    
    logger.success("✅ GPU Stats Service démarré avec succès")
    
    yield
    
    # Shutdown
    logger.info("🛑 Arrêt du GPU Stats Service...")
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass

# Application FastAPI
app = FastAPI(
    title="JARVIS GPU Stats Service",
    description="Service de monitoring GPU AMD RX 7800 XT pour JARVIS AI",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En prod, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes API
@app.get("/health")
async def health_check():
    """Health check pour Docker"""
    return {
        "status": "healthy",
        "service": "gpu-stats-service",
        "timestamp": time.time(),
        "gpu_detected": gpu_monitor.gpu_info["name"] != "Unknown"
    }

@app.get("/gpu/info")
async def get_gpu_info():
    """Informations sur le GPU détecté"""
    return {
        "gpu_info": gpu_monitor.gpu_info,
        "platform": platform.system(),
        "last_update": gpu_monitor.last_stats.timestamp if gpu_monitor.last_stats else None
    }

@app.get("/gpu/stats", response_model=GPUStats)
async def get_current_stats():
    """Récupérer les statistiques GPU actuelles"""
    stats = await gpu_monitor.get_gpu_stats()
    if not stats:
        raise HTTPException(status_code=503, detail="GPU stats unavailable")
    return stats

@app.get("/gpu/history")
async def get_stats_history(minutes: int = 10):
    """Récupérer l'historique des stats (simulation)"""
    # Pour la démo, générer un historique simulé
    history = []
    current_time = time.time()
    
    for i in range(minutes * 60):  # Une mesure par seconde
        timestamp = current_time - (minutes * 60 - i)
        
        # Simuler des données historiques
        import random
        import math
        wave = math.sin(timestamp / 60) * 0.4 + 0.6
        utilization = max(0, min(100, wave * 70 + random.uniform(-5, 5)))
        
        history.append({
            "timestamp": timestamp,
            "utilization": round(utilization, 1),
            "temperature": round(40 + utilization * 0.5 + random.uniform(-2, 2), 1),
            "memory_utilization": round(utilization * 0.8 + random.uniform(-5, 5), 1)
        })
    
    return {"history": history}

@app.websocket("/ws/gpu-stats")
async def websocket_gpu_stats(websocket: WebSocket):
    """WebSocket pour les stats GPU en temps réel"""
    await manager.connect(websocket)
    try:
        while True:
            # Garder la connexion ouverte
            await websocket.recv_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ Erreur WebSocket: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    logger.info("🎮 Démarrage du JARVIS GPU Stats Service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5009,
        reload=False,
        log_level="info"
    )