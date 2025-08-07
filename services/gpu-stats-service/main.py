"""
🎮 GPU Stats Service - JARVIS AI
Cross-platform GPU monitoring service for JARVIS AI
Supports NVIDIA, AMD GPUs with graceful fallbacks
"""

import asyncio
import json
import time
import subprocess
import platform
import re
import os
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger
import uvicorn

# Cross-platform GPU monitoring imports
try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False
    logger.warning("GPUtil not available - will use basic monitoring")

try:
    import py3nvml.py3nvml as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    logger.warning("NVML not available - NVIDIA GPU monitoring disabled")

try:
    import distro
    DISTRO_AVAILABLE = True
except ImportError:
    DISTRO_AVAILABLE = False

# Configuration du logger
logger.add("gpu_stats.log", rotation="1 MB", retention="7 days", level="INFO")

class GPUStats(BaseModel):
    """Cross-platform GPU statistics model"""
    name: str = "Unknown GPU"
    temperature: float = 0.0
    utilization: float = 0.0
    memory_used: float = 0.0
    memory_total: float = 0.0
    memory_utilization: float = 0.0
    core_clock: int = 0
    memory_clock: int = 0
    power_usage: float = 0.0
    fan_speed: int = 0
    driver_version: str = "Unknown"
    timestamp: float
    status: str = "healthy"
    gpu_type: str = "unknown"  # nvidia, amd, intel, unknown
    monitoring_method: str = "simulation"  # nvml, gputil, rocm, simulation

class GPUMonitor:
    """Cross-platform GPU monitor with fallback support"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.gpu_info = {
            "name": "Unknown GPU",
            "memory_total": 0,  # MB
            "driver_version": "Unknown",
            "gpu_type": "unknown",
            "monitoring_method": "simulation"
        }
        self.last_stats = None
        self.nvml_initialized = False
        self.gpus_detected = []
        
    async def initialize(self):
        """Initialize cross-platform GPU monitor"""
        try:
            logger.info("🚀 Initializing cross-platform GPU monitor...")
            
            # Try different detection methods in order of preference
            success = False
            
            # Method 1: NVIDIA GPUs via NVML
            if await self._detect_nvidia_gpu():
                success = True
                
            # Method 2: General GPU detection via GPUtil
            if not success and await self._detect_via_gputil():
                success = True
            
            # Method 3: System-specific detection
            if not success and await self._detect_system_gpu():
                success = True
            
            # Test stats retrieval
            test_stats = await self.get_gpu_stats()
            if test_stats:
                logger.success(f"✅ GPU monitor initialized - Method: {self.gpu_info['monitoring_method']}")
                return True
            else:
                logger.warning("⚠️ GPU monitor running in simulation mode")
                self.gpu_info["monitoring_method"] = "simulation"
                return True
                
        except Exception as e:
            logger.error(f"❌ GPU monitor initialization error: {e}")
            self.gpu_info["monitoring_method"] = "simulation"
            return False
    
    async def _detect_nvidia_gpu(self) -> bool:
        """Detect NVIDIA GPUs using NVML"""
        if not NVML_AVAILABLE:
            return False
            
        try:
            nvml.nvmlInit()
            self.nvml_initialized = True
            
            device_count = nvml.nvmlDeviceGetCount()
            if device_count > 0:
                # Use first GPU
                handle = nvml.nvmlDeviceGetHandleByIndex(0)
                name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # Get memory info
                mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                memory_total_mb = mem_info.total // (1024 * 1024)
                
                # Get driver version
                try:
                    driver_version = nvml.nvmlSystemGetDriverVersion().decode('utf-8')
                except:
                    driver_version = "Unknown"
                
                self.gpu_info.update({
                    "name": name,
                    "memory_total": memory_total_mb,
                    "driver_version": driver_version,
                    "gpu_type": "nvidia",
                    "monitoring_method": "nvml"
                })
                
                logger.info(f"🎮 NVIDIA GPU detected via NVML: {name}")
                return True
                
        except Exception as e:
            logger.debug(f"NVML detection failed: {e}")
            self.nvml_initialized = False
            
        return False
    
    async def _detect_via_gputil(self) -> bool:
        """Detect GPUs using GPUtil library"""
        if not GPUTIL_AVAILABLE:
            return False
            
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Use first GPU
                
                self.gpu_info.update({
                    "name": gpu.name,
                    "memory_total": int(gpu.memoryTotal),
                    "driver_version": getattr(gpu, 'driver', 'Unknown'),
                    "gpu_type": "nvidia" if "nvidia" in gpu.name.lower() else "amd" if "amd" in gpu.name.lower() else "unknown",
                    "monitoring_method": "gputil"
                })
                
                logger.info(f"🎮 GPU detected via GPUtil: {gpu.name}")
                return True
                
        except Exception as e:
            logger.debug(f"GPUtil detection failed: {e}")
            
        return False
    
    async def _detect_system_gpu(self) -> bool:
        """Detect GPU using system-specific methods"""
        try:
            if self.platform == "linux":
                return await self._detect_linux_gpu()
            elif self.platform == "windows":
                return await self._detect_windows_gpu()
            elif self.platform == "darwin":
                return await self._detect_macos_gpu()
        except Exception as e:
            logger.debug(f"System GPU detection failed: {e}")
            
        return False
    
    async def _detect_linux_gpu(self) -> bool:
        """Detect GPU on Linux systems"""
        try:
            # Try lspci for GPU detection
            result = subprocess.run(["lspci", "-v"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                lines = result.stdout.lower()
                
                # Look for GPU entries
                if "amd" in lines and ("radeon" in lines or "amdgpu" in lines):
                    # Try ROCm for AMD GPUs
                    if await self._try_rocm():
                        return True
                    
                    # Fallback AMD detection
                    self.gpu_info.update({
                        "name": "AMD GPU (detected via lspci)",
                        "memory_total": 8192,  # Default assumption
                        "gpu_type": "amd",
                        "monitoring_method": "system"
                    })
                    logger.info("🎮 AMD GPU detected via lspci")
                    return True
                    
                elif "nvidia" in lines:
                    self.gpu_info.update({
                        "name": "NVIDIA GPU (detected via lspci)",
                        "memory_total": 8192,  # Default assumption
                        "gpu_type": "nvidia",
                        "monitoring_method": "system"
                    })
                    logger.info("🎮 NVIDIA GPU detected via lspci")
                    return True
                    
        except Exception as e:
            logger.debug(f"Linux GPU detection failed: {e}")
            
        return False
    
    async def _try_rocm(self) -> bool:
        """Try to get AMD GPU info via ROCm"""
        try:
            result = subprocess.run(["rocm-smi", "--showid"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.gpu_info.update({
                    "name": "AMD GPU (ROCm)",
                    "monitoring_method": "rocm"
                })
                logger.info("🎮 AMD GPU with ROCm support detected")
                return True
        except Exception:
            pass
        return False
    
    async def _detect_windows_gpu(self) -> bool:
        """Detect GPU on Windows (without WMI)"""
        try:
            # Use PowerShell without WMI dependencies
            cmd = [
                "powershell", "-Command",
                "Get-CimInstance -ClassName Win32_VideoController | Where-Object {$_.Name -notlike '*Microsoft*'} | Select-Object Name, AdapterRAM | ConvertTo-Json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    if isinstance(data, list) and data:
                        gpu = data[0]
                    elif isinstance(data, dict):
                        gpu = data
                    else:
                        return False
                    
                    name = gpu.get("Name", "Unknown GPU")
                    memory_ram = gpu.get("AdapterRAM", 0)
                    memory_mb = memory_ram // (1024 * 1024) if memory_ram else 4096
                    
                    gpu_type = "nvidia" if "nvidia" in name.lower() else "amd" if "amd" in name.lower() else "unknown"
                    
                    self.gpu_info.update({
                        "name": name,
                        "memory_total": memory_mb,
                        "gpu_type": gpu_type,
                        "monitoring_method": "system"
                    })
                    
                    logger.info(f"🎮 GPU detected on Windows: {name}")
                    return True
                    
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logger.debug(f"Windows GPU detection failed: {e}")
            
        return False
    
    async def _detect_macos_gpu(self) -> bool:
        """Detect GPU on macOS"""
        try:
            result = subprocess.run(["system_profiler", "SPDisplaysDataType", "-json"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                displays = data.get("SPDisplaysDataType", [])
                
                for display in displays:
                    if "sppci_model" in display:
                        name = display["sppci_model"]
                        memory = display.get("sppci_vram", "0 MB")
                        
                        # Parse memory
                        memory_mb = 0
                        if "MB" in memory:
                            memory_mb = int(re.search(r'(\d+)', memory).group(1))
                        elif "GB" in memory:
                            memory_mb = int(re.search(r'(\d+)', memory).group(1)) * 1024
                        
                        self.gpu_info.update({
                            "name": name,
                            "memory_total": memory_mb,
                            "gpu_type": "apple" if "apple" in name.lower() else "amd" if "amd" in name.lower() else "unknown",
                            "monitoring_method": "system"
                        })
                        
                        logger.info(f"🎮 GPU detected on macOS: {name}")
                        return True
                        
        except Exception as e:
            logger.debug(f"macOS GPU detection failed: {e}")
            
        return False
    
    async def get_gpu_stats(self) -> Optional[GPUStats]:
        """Get current GPU statistics using the best available method"""
        try:
            stats_data = None
            
            # Try different methods based on what was detected
            if self.gpu_info["monitoring_method"] == "nvml" and self.nvml_initialized:
                stats_data = await self._get_stats_nvml()
            elif self.gpu_info["monitoring_method"] == "gputil" and GPUTIL_AVAILABLE:
                stats_data = await self._get_stats_gputil()
            elif self.gpu_info["monitoring_method"] == "rocm":
                stats_data = await self._get_stats_rocm()
            elif self.gpu_info["monitoring_method"] == "system":
                stats_data = await self._get_stats_system()
            
            # Fallback to simulation
            if not stats_data:
                stats_data = await self._simulate_gpu_stats()
            
            # Create GPUStats object
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
                status="healthy" if stats_data.get("temperature", 0) < 85 else "warning",
                gpu_type=self.gpu_info["gpu_type"],
                monitoring_method=self.gpu_info["monitoring_method"]
            )
            
            self.last_stats = gpu_stats
            return gpu_stats
            
        except Exception as e:
            logger.error(f"❌ Error retrieving GPU stats: {e}")
            return None
    
    async def _get_stats_nvml(self) -> Optional[Dict]:
        """Get stats via NVIDIA NVML"""
        try:
            handle = nvml.nvmlDeviceGetHandleByIndex(0)
            
            # Temperature
            temp = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
            
            # Utilization
            util = nvml.nvmlDeviceGetUtilizationRates(handle)
            
            # Memory
            mem_info = nvml.nvmlDeviceGetMemoryInfo(handle)
            memory_used_mb = mem_info.used // (1024 * 1024)
            memory_util = (mem_info.used / mem_info.total) * 100
            
            # Power (if available)
            power = 0
            try:
                power = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
            except:
                pass
            
            # Clock speeds
            core_clock = 0
            memory_clock = 0
            try:
                core_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_GRAPHICS)
                memory_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_MEM)
            except:
                pass
            
            # Fan speed
            fan_speed = 0
            try:
                fan_speed = nvml.nvmlDeviceGetFanSpeed(handle)
            except:
                pass
            
            return {
                "temperature": float(temp),
                "utilization": float(util.gpu),
                "memory_used": float(memory_used_mb),
                "memory_utilization": float(memory_util),
                "core_clock": int(core_clock),
                "memory_clock": int(memory_clock),
                "power_usage": float(power),
                "fan_speed": int(fan_speed)
            }
            
        except Exception as e:
            logger.debug(f"NVML stats retrieval failed: {e}")
            return None
    
    async def _get_stats_gputil(self) -> Optional[Dict]:
        """Get stats via GPUtil"""
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                
                return {
                    "temperature": float(gpu.temperature),
                    "utilization": float(gpu.load * 100),
                    "memory_used": float(gpu.memoryUsed),
                    "memory_utilization": float((gpu.memoryUsed / gpu.memoryTotal) * 100),
                    "core_clock": 0,  # Not available in GPUtil
                    "memory_clock": 0,
                    "power_usage": 0.0,
                    "fan_speed": 0
                }
                
        except Exception as e:
            logger.debug(f"GPUtil stats retrieval failed: {e}")
            return None
    
    async def _get_stats_rocm(self) -> Optional[Dict]:
        """Get stats via ROCm for AMD GPUs"""
        try:
            result = subprocess.run(
                ["rocm-smi", "--showtemp", "--showuse", "--showmemuse", "--showclocks"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
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
                
                # Add default values for missing data
                stats.setdefault('memory_used', 0.0)
                stats.setdefault('memory_utilization', 0.0)
                stats.setdefault('core_clock', 0)
                stats.setdefault('memory_clock', 0)
                stats.setdefault('power_usage', 0.0)
                stats.setdefault('fan_speed', 0)
                
                return stats if stats else None
                
        except Exception as e:
            logger.debug(f"ROCm stats retrieval failed: {e}")
            return None
    
    async def _get_stats_system(self) -> Optional[Dict]:
        """Get basic stats using system monitoring"""
        try:
            # Use psutil for basic system stats as proxy
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Estimate GPU usage based on system load
            estimated_gpu_usage = min(cpu_percent * 1.2, 100.0)
            
            return {
                "temperature": 45.0 + (estimated_gpu_usage * 0.4),
                "utilization": estimated_gpu_usage,
                "memory_used": (estimated_gpu_usage * self.gpu_info["memory_total"]) / 100,
                "memory_utilization": estimated_gpu_usage * 0.8,
                "core_clock": 1500,  # Generic default
                "memory_clock": 1500,
                "power_usage": 100.0 + (estimated_gpu_usage * 1.5),
                "fan_speed": int(30 + (estimated_gpu_usage * 0.5))
            }
            
        except Exception as e:
            logger.debug(f"System stats retrieval failed: {e}")
            return None
    
    async def _simulate_gpu_stats(self) -> Dict:
        """Simulate realistic GPU statistics"""
        import random
        import math
        
        # Realistic simulation based on time patterns
        base_time = time.time()
        wave = math.sin(base_time / 30) * 0.3 + 0.7  # Slow wave
        noise = random.uniform(0.9, 1.1)  # Random noise
        
        utilization = max(0, min(100, (wave * 60 + random.uniform(-10, 15)) * noise))
        temperature = 35 + (utilization * 0.6) + random.uniform(-2, 3)
        
        # Ensure memory_total is set for simulation
        if self.gpu_info["memory_total"] == 0:
            self.gpu_info["memory_total"] = 8192  # Default 8GB
        
        memory_used = (utilization / 100) * self.gpu_info["memory_total"] * random.uniform(0.8, 1.2)
        memory_utilization = (memory_used / self.gpu_info["memory_total"]) * 100
        
        return {
            "temperature": round(temperature, 1),
            "utilization": round(utilization, 1),
            "memory_used": round(memory_used, 1),
            "memory_utilization": round(memory_utilization, 1),
            "core_clock": random.randint(1200, 2600),
            "memory_clock": random.randint(1000, 2500),
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
        logger.info(f"📡 New WebSocket connection. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"📡 WebSocket connection closed. Total: {len(self.active_connections)}")

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
                logger.error(f"WebSocket broadcast error: {e}")
                disconnected.append(connection)
        
        # Clean up closed connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Real-time broadcast task
async def broadcast_gpu_stats():
    """Broadcast GPU stats in real-time via WebSocket"""
    while True:
        try:
            stats = await gpu_monitor.get_gpu_stats()
            if stats and manager.active_connections:
                await manager.broadcast({
                    "type": "gpu_stats",
                    "data": stats.dict()
                })
            
            await asyncio.sleep(1)  # Update every second
            
        except Exception as e:
            logger.error(f"❌ Broadcast stats error: {e}")
            await asyncio.sleep(5)

# Application lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting GPU Stats Service...")
    
    # Initialize GPU monitor
    await gpu_monitor.initialize()
    
    # Start broadcast task
    broadcast_task = asyncio.create_task(broadcast_gpu_stats())
    
    logger.success("✅ GPU Stats Service started successfully")
    
    yield
    
    # Shutdown
    logger.info("🛑 Stopping GPU Stats Service...")
    broadcast_task.cancel()
    try:
        await broadcast_task
    except asyncio.CancelledError:
        pass

# FastAPI application
app = FastAPI(
    title="JARVIS GPU Stats Service",
    description="Cross-platform GPU monitoring service for JARVIS AI",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/health")
async def health_check():
    """Health check for Docker"""
    return {
        "status": "healthy",
        "service": "gpu-stats-service",
        "timestamp": time.time(),
        "gpu_detected": gpu_monitor.gpu_info["name"] != "Unknown GPU",
        "monitoring_method": gpu_monitor.gpu_info["monitoring_method"]
    }

@app.get("/gpu/info")
async def get_gpu_info():
    """Information about detected GPU"""
    return {
        "gpu_info": gpu_monitor.gpu_info,
        "platform": platform.system(),
        "last_update": gpu_monitor.last_stats.timestamp if gpu_monitor.last_stats else None,
        "capabilities": {
            "nvml_available": NVML_AVAILABLE,
            "gputil_available": GPUTIL_AVAILABLE,
            "distro_available": DISTRO_AVAILABLE
        }
    }

@app.get("/gpu/stats", response_model=GPUStats)
async def get_current_stats():
    """Get current GPU statistics"""
    stats = await gpu_monitor.get_gpu_stats()
    if not stats:
        raise HTTPException(status_code=503, detail="GPU stats unavailable")
    return stats

@app.get("/gpu/history")
async def get_stats_history(minutes: int = 10):
    """Get GPU stats history (simulated)"""
    history = []
    current_time = time.time()
    
    for i in range(minutes * 60):  # One measurement per second
        timestamp = current_time - (minutes * 60 - i)
        
        # Simulate historical data
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
    """WebSocket for real-time GPU stats"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection open
            await websocket.recv_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    logger.info("🎮 Starting JARVIS GPU Stats Service...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5009,
        reload=False,
        log_level="info"
    )