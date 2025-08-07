"""
🎮 GPU Monitor - Real-time AMD RX 7800 XT Monitoring
Surveillance en temps réel des métriques GPU pour optimisation LLM
"""

import asyncio
import time
import json
import subprocess
import psutil
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class GPUVendor(Enum):
    AMD = "amd"
    NVIDIA = "nvidia"
    INTEL = "intel"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"

@dataclass
class GPUMetrics:
    """Métriques GPU complètes"""
    # Identification
    vendor: GPUVendor
    name: str
    driver_version: str
    
    # Mémoire VRAM
    memory_used_mb: int
    memory_total_mb: int
    memory_free_mb: int
    memory_utilization_percent: float
    
    # Performance
    gpu_utilization_percent: float
    compute_units_active: int
    clock_speed_mhz: int
    memory_clock_mhz: int
    
    # Thermique
    temperature_c: float
    fan_speed_percent: float
    power_draw_watts: float
    
    # État système
    processes: List[Dict[str, Any]]
    timestamp: float
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp'):
            self.timestamp = time.time()

@dataclass 
class GPUAlert:
    level: AlertLevel
    message: str
    metric_name: str
    current_value: float
    threshold_value: float
    timestamp: float
    
    def __post_init__(self):
        if not hasattr(self, 'timestamp'):
            self.timestamp = time.time()

class GPUMonitor:
    """Monitor GPU en temps réel pour AMD RX 7800 XT"""
    
    def __init__(self, monitoring_interval: float = 5.0):
        self.monitoring_interval = monitoring_interval
        self.vendor = GPUVendor.UNKNOWN
        
        # État monitoring
        self.is_monitoring = False
        self.current_metrics: Optional[GPUMetrics] = None
        self.metrics_history: List[GPUMetrics] = []
        self.max_history_size = 720  # 1 heure à 5s d'intervalle
        
        # Alertes et seuils
        self.alert_callbacks: List[Callable[[GPUAlert], None]] = []
        self.active_alerts: List[GPUAlert] = []
        
        # Seuils par défaut AMD RX 7800 XT
        self.thresholds = {
            "memory_utilization_warning": 80.0,    # 80% VRAM
            "memory_utilization_critical": 90.0,   # 90% VRAM
            "temperature_warning": 80.0,           # 80°C
            "temperature_critical": 85.0,          # 85°C
            "gpu_utilization_high": 95.0,          # 95% GPU
            "power_draw_warning": 250.0,           # 250W
            "fan_speed_warning": 80.0              # 80% fan
        }
        
        # Statistiques
        self.stats = {
            "monitoring_start_time": 0,
            "total_samples": 0,
            "alerts_generated": 0,
            "avg_temperature": 0.0,
            "avg_memory_usage": 0.0,
            "max_temperature": 0.0,
            "max_memory_usage": 0.0
        }
    
    async def initialize(self):
        """Initialisation du monitoring GPU"""
        logger.info("🎮 Initialisation GPU Monitor...")
        
        # Détecter GPU et vendor
        await self._detect_gpu()
        
        # Tester accès aux métriques
        await self._test_metrics_access()
        
        logger.info(f"✅ GPU Monitor initialisé: {self.vendor.value} GPU détecté")
    
    async def _detect_gpu(self):
        """Détection automatique GPU et vendor"""
        try:
            # Tenter ROCm (AMD)
            result = subprocess.run(
                ["rocm-smi", "--showproductname"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0 and "RX 7800 XT" in result.stdout:
                self.vendor = GPUVendor.AMD
                logger.info("🔴 GPU AMD RX 7800 XT détecté")
                return
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Tenter nvidia-smi (NVIDIA)
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                self.vendor = GPUVendor.NVIDIA
                logger.info("🟢 GPU NVIDIA détecté")
                return
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback détection générique
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                if "AMD" in gpu.name or "Radeon" in gpu.name:
                    self.vendor = GPUVendor.AMD
                elif "NVIDIA" in gpu.name or "GeForce" in gpu.name or "RTX" in gpu.name:
                    self.vendor = GPUVendor.NVIDIA
                else:
                    self.vendor = GPUVendor.UNKNOWN
                
                logger.info(f"📊 GPU détecté via GPUtil: {gpu.name}")
                return
                
        except ImportError:
            pass
        
        logger.warning("⚠️ Aucun GPU détecté ou outils monitoring manquants")
        self.vendor = GPUVendor.UNKNOWN
    
    async def _test_metrics_access(self):
        """Test accès aux métriques GPU"""
        try:
            metrics = await self._collect_metrics()
            if metrics:
                logger.info("✅ Accès métriques GPU confirmé")
            else:
                logger.warning("⚠️ Métriques GPU limitées ou indisponibles")
        except Exception as e:
            logger.error(f"❌ Erreur test métriques: {e}")
    
    async def _collect_metrics(self) -> Optional[GPUMetrics]:
        """Collecte métriques GPU selon vendor"""
        
        if self.vendor == GPUVendor.AMD:
            return await self._collect_amd_metrics()
        elif self.vendor == GPUVendor.NVIDIA:
            return await self._collect_nvidia_metrics()
        else:
            return await self._collect_generic_metrics()
    
    async def _collect_amd_metrics(self) -> Optional[GPUMetrics]:
        """Collecte métriques AMD via rocm-smi"""
        try:
            # Commande rocm-smi complète
            cmd = [
                "rocm-smi",
                "--showmeminfo", "vram",
                "--showuse",
                "--showtemp",
                "--showclocks",
                "--showpower",
                "--showfan",
                "--showproductname",
                "--showdriverversion",
                "--json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Parser données rocm-smi (format peut varier)
                card_data = data.get("card0", {})
                
                # Extraction métriques
                memory_used = int(card_data.get("VRAM Total Memory (B)", 0)) // (1024 * 1024)
                memory_total = int(card_data.get("VRAM Total Memory (B)", 16384 * 1024 * 1024)) // (1024 * 1024)
                memory_free = memory_total - memory_used
                memory_util = (memory_used / memory_total) * 100 if memory_total > 0 else 0
                
                gpu_util = float(card_data.get("GPU use (%)", 0))
                temp = float(card_data.get("Temperature (Sensor edge) (C)", 0))
                fan_speed = float(card_data.get("Fan speed (%)", 0))
                power = float(card_data.get("Average Graphics Package Power (W)", 0))
                
                gpu_clock = int(card_data.get("sclk clock speed", 0))
                mem_clock = int(card_data.get("mclk clock speed", 0))
                
                return GPUMetrics(
                    vendor=GPUVendor.AMD,
                    name=card_data.get("Card series", "AMD RX 7800 XT"),
                    driver_version=card_data.get("Driver version", "unknown"),
                    memory_used_mb=memory_used,
                    memory_total_mb=memory_total,
                    memory_free_mb=memory_free,
                    memory_utilization_percent=memory_util,
                    gpu_utilization_percent=gpu_util,
                    compute_units_active=60,  # RX 7800 XT spec
                    clock_speed_mhz=gpu_clock,
                    memory_clock_mhz=mem_clock,
                    temperature_c=temp,
                    fan_speed_percent=fan_speed,
                    power_draw_watts=power,
                    processes=await self._get_gpu_processes(),
                    timestamp=time.time()
                )
                
        except Exception as e:
            logger.error(f"❌ Erreur métriques AMD: {e}")
            
        return None
    
    async def _collect_nvidia_metrics(self) -> Optional[GPUMetrics]:
        """Collecte métriques NVIDIA via nvidia-smi"""
        try:
            cmd = [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.used,memory.total,memory.free,utilization.gpu,temperature.gpu,fan.speed,power.draw,clocks.gr,clocks.mem",
                "--format=csv,noheader,nounits"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                values = result.stdout.strip().split(", ")
                
                return GPUMetrics(
                    vendor=GPUVendor.NVIDIA,
                    name=values[0],
                    driver_version=values[1],
                    memory_used_mb=int(values[2]),
                    memory_total_mb=int(values[3]),
                    memory_free_mb=int(values[4]),
                    memory_utilization_percent=(int(values[2]) / int(values[3])) * 100,
                    gpu_utilization_percent=float(values[5]),
                    compute_units_active=0,  # N/A pour NVIDIA
                    clock_speed_mhz=int(values[9]),
                    memory_clock_mhz=int(values[10]),
                    temperature_c=float(values[6]),
                    fan_speed_percent=float(values[7]) if values[7] != "[Not Supported]" else 0,
                    power_draw_watts=float(values[8]) if values[8] != "[Not Supported]" else 0,
                    processes=await self._get_gpu_processes(),
                    timestamp=time.time()
                )
                
        except Exception as e:
            logger.error(f"❌ Erreur métriques NVIDIA: {e}")
            
        return None
    
    async def _collect_generic_metrics(self) -> Optional[GPUMetrics]:
        """Collecte métriques générique via GPUtil"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            
            if gpus:
                gpu = gpus[0]  # Premier GPU
                
                return GPUMetrics(
                    vendor=GPUVendor.UNKNOWN,
                    name=gpu.name,
                    driver_version="unknown",
                    memory_used_mb=int(gpu.memoryUsed),
                    memory_total_mb=int(gpu.memoryTotal),
                    memory_free_mb=int(gpu.memoryFree),
                    memory_utilization_percent=gpu.memoryUtil * 100,
                    gpu_utilization_percent=gpu.load * 100,
                    compute_units_active=0,
                    clock_speed_mhz=0,
                    memory_clock_mhz=0,
                    temperature_c=gpu.temperature,
                    fan_speed_percent=0,
                    power_draw_watts=0,
                    processes=[],
                    timestamp=time.time()
                )
                
        except Exception as e:
            logger.error(f"❌ Erreur métriques génériques: {e}")
            
        return None
    
    async def _get_gpu_processes(self) -> List[Dict[str, Any]]:
        """Récupérer processus utilisant GPU"""
        processes = []
        
        try:
            if self.vendor == GPUVendor.NVIDIA:
                result = subprocess.run(
                    ["nvidia-smi", "--query-compute-apps=pid,name,used_memory", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            pid, name, memory = line.split(', ')
                            processes.append({
                                "pid": int(pid),
                                "name": name,
                                "memory_mb": int(memory)
                            })
            
            # Pour AMD, pas d'équivalent direct rocm-smi, utiliser approche générique
            elif self.vendor == GPUVendor.AMD:
                # Chercher processus "ollama" ou "python" utilisant GPU
                for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
                    try:
                        if proc.info['name'] in ['ollama', 'python', 'python.exe']:
                            processes.append({
                                "pid": proc.info['pid'],
                                "name": proc.info['name'],
                                "memory_mb": proc.info['memory_info'].rss // (1024 * 1024)
                            })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
        except Exception as e:
            logger.debug(f"Erreur récupération processus GPU: {e}")
        
        return processes
    
    def _check_thresholds(self, metrics: GPUMetrics):
        """Vérification seuils et génération alertes"""
        alerts_to_add = []
        
        # Vérifier utilisation mémoire
        if metrics.memory_utilization_percent >= self.thresholds["memory_utilization_critical"]:
            alert = GPUAlert(
                level=AlertLevel.CRITICAL,
                message=f"VRAM critique: {metrics.memory_utilization_percent:.1f}% utilisée",
                metric_name="memory_utilization",
                current_value=metrics.memory_utilization_percent,
                threshold_value=self.thresholds["memory_utilization_critical"],
                timestamp=time.time()
            )
            alerts_to_add.append(alert)
            
        elif metrics.memory_utilization_percent >= self.thresholds["memory_utilization_warning"]:
            alert = GPUAlert(
                level=AlertLevel.WARNING,
                message=f"VRAM élevée: {metrics.memory_utilization_percent:.1f}% utilisée",
                metric_name="memory_utilization",
                current_value=metrics.memory_utilization_percent,
                threshold_value=self.thresholds["memory_utilization_warning"],
                timestamp=time.time()
            )
            alerts_to_add.append(alert)
        
        # Vérifier température
        if metrics.temperature_c >= self.thresholds["temperature_critical"]:
            alert = GPUAlert(
                level=AlertLevel.CRITICAL,
                message=f"Température critique: {metrics.temperature_c}°C",
                metric_name="temperature",
                current_value=metrics.temperature_c,
                threshold_value=self.thresholds["temperature_critical"],
                timestamp=time.time()
            )
            alerts_to_add.append(alert)
            
        elif metrics.temperature_c >= self.thresholds["temperature_warning"]:
            alert = GPUAlert(
                level=AlertLevel.WARNING,
                message=f"Température élevée: {metrics.temperature_c}°C",
                metric_name="temperature",
                current_value=metrics.temperature_c,
                threshold_value=self.thresholds["temperature_warning"],
                timestamp=time.time()
            )
            alerts_to_add.append(alert)
        
        # Ajouter nouvelles alertes
        for alert in alerts_to_add:
            self.active_alerts.append(alert)
            self.stats["alerts_generated"] += 1
            
            # Notifier callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"❌ Erreur callback alerte: {e}")
    
    async def start_monitoring(self):
        """Démarrer monitoring en continu"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.stats["monitoring_start_time"] = time.time()
        
        logger.info("🔄 Démarrage monitoring GPU...")
        
        try:
            while self.is_monitoring:
                metrics = await self._collect_metrics()
                
                if metrics:
                    self.current_metrics = metrics
                    self.metrics_history.append(metrics)
                    
                    # Limiter historique
                    if len(self.metrics_history) > self.max_history_size:
                        self.metrics_history.pop(0)
                    
                    # Vérifier seuils
                    self._check_thresholds(metrics)
                    
                    # Mise à jour statistiques
                    self._update_stats(metrics)
                    
                    self.stats["total_samples"] += 1
                
                await asyncio.sleep(self.monitoring_interval)
                
        except Exception as e:
            logger.error(f"❌ Erreur monitoring GPU: {e}")
        finally:
            self.is_monitoring = False
            logger.info("🛑 Monitoring GPU arrêté")
    
    def _update_stats(self, metrics: GPUMetrics):
        """Mise à jour statistiques cumulées"""
        total_samples = self.stats["total_samples"]
        
        # Moyennes mobiles
        self.stats["avg_temperature"] = (
            (self.stats["avg_temperature"] * total_samples + metrics.temperature_c) / 
            (total_samples + 1)
        )
        
        self.stats["avg_memory_usage"] = (
            (self.stats["avg_memory_usage"] * total_samples + metrics.memory_utilization_percent) / 
            (total_samples + 1)
        )
        
        # Maxima
        self.stats["max_temperature"] = max(self.stats["max_temperature"], metrics.temperature_c)
        self.stats["max_memory_usage"] = max(self.stats["max_memory_usage"], metrics.memory_utilization_percent)
    
    def stop_monitoring(self):
        """Arrêter monitoring"""
        self.is_monitoring = False
    
    def add_alert_callback(self, callback: Callable[[GPUAlert], None]):
        """Ajouter callback pour alertes"""
        self.alert_callbacks.append(callback)
    
    def get_current_metrics(self) -> Optional[Dict[str, Any]]:
        """Récupérer métriques actuelles"""
        if self.current_metrics:
            return asdict(self.current_metrics)
        return None
    
    def get_metrics_history(self, last_minutes: int = 10) -> List[Dict[str, Any]]:
        """Récupérer historique métriques"""
        cutoff_time = time.time() - (last_minutes * 60)
        
        filtered_metrics = [
            asdict(m) for m in self.metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        return filtered_metrics
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Récupérer alertes actives"""
        # Nettoyer alertes anciennes (> 5 minutes)
        cutoff_time = time.time() - 300
        self.active_alerts = [a for a in self.active_alerts if a.timestamp >= cutoff_time]
        
        return [asdict(a) for a in self.active_alerts]
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupérer statistiques monitoring"""
        uptime = time.time() - self.stats["monitoring_start_time"] if self.stats["monitoring_start_time"] > 0 else 0
        
        return {
            **self.stats,
            "monitoring_uptime_seconds": uptime,
            "is_monitoring": self.is_monitoring,
            "vendor": self.vendor.value,
            "history_size": len(self.metrics_history),
            "active_alerts_count": len(self.active_alerts)
        }
    
    async def shutdown(self):
        """Arrêt propre monitor"""
        logger.info("🛑 Arrêt GPU Monitor...")
        
        self.stop_monitoring()
        
        # Attendre arrêt complet
        await asyncio.sleep(1)
        
        logger.info("✅ GPU Monitor arrêté")