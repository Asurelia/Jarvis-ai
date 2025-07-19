"""
Détecteur d'applications pour JARVIS
Détecte et gère les applications Windows actives
"""
import asyncio
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import psutil
import subprocess
from loguru import logger

# Import conditionnel pour Windows
try:
    import win32gui
    import win32process
    import win32con
    import win32api
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logger.warning("Modules Windows non disponibles - fonctionnalités limitées")

@dataclass
class WindowInfo:
    """Informations sur une fenêtre"""
    hwnd: int
    title: str
    class_name: str
    process_id: int
    process_name: str
    executable_path: str
    is_visible: bool
    is_active: bool
    bounds: Tuple[int, int, int, int]  # left, top, right, bottom
    
    @property
    def width(self) -> int:
        return self.bounds[2] - self.bounds[0]
    
    @property
    def height(self) -> int:
        return self.bounds[3] - self.bounds[1]
    
    @property
    def center(self) -> Tuple[int, int]:
        return (
            self.bounds[0] + self.width // 2,
            self.bounds[1] + self.height // 2
        )

@dataclass
class ApplicationInfo:
    """Informations sur une application"""
    process_id: int
    name: str
    executable_path: str
    command_line: str
    memory_usage: int  # En MB
    cpu_percent: float
    create_time: float
    windows: List[WindowInfo]
    is_active: bool = False
    
    @property
    def main_window(self) -> Optional[WindowInfo]:
        """Retourne la fenêtre principale de l'application"""
        if not self.windows:
            return None
        
        # Priorité à la fenêtre active
        for window in self.windows:
            if window.is_active:
                return window
        
        # Sinon, la plus grande fenêtre visible
        visible_windows = [w for w in self.windows if w.is_visible and w.title]
        if visible_windows:
            return max(visible_windows, key=lambda w: w.width * w.height)
        
        return self.windows[0] if self.windows else None

class WindowsAppDetector:
    """Détecteur d'applications Windows natif"""
    
    def __init__(self):
        self.enabled = WINDOWS_AVAILABLE
        if not self.enabled:
            logger.warning("Détecteur Windows non disponible")
    
    def get_all_windows(self) -> List[WindowInfo]:
        """Récupère toutes les fenêtres"""
        if not self.enabled:
            return []
        
        windows = []
        
        def enum_windows_callback(hwnd, _):
            try:
                if win32gui.IsWindow(hwnd) and win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    
                    # Ignorer les fenêtres sans titre ou système
                    if not title or title.isspace():
                        return True
                    
                    # Récupérer les informations du processus
                    try:
                        thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(process_id)
                        process_name = process.name()
                        executable_path = process.exe()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_id = 0
                        process_name = "Unknown"
                        executable_path = ""
                    
                    # Récupérer les dimensions
                    try:
                        bounds = win32gui.GetWindowRect(hwnd)
                    except:
                        bounds = (0, 0, 0, 0)
                    
                    # Vérifier si c'est la fenêtre active
                    is_active = win32gui.GetForegroundWindow() == hwnd
                    
                    window_info = WindowInfo(
                        hwnd=hwnd,
                        title=title,
                        class_name=class_name,
                        process_id=process_id,
                        process_name=process_name,
                        executable_path=executable_path,
                        is_visible=True,
                        is_active=is_active,
                        bounds=bounds
                    )
                    
                    windows.append(window_info)
            
            except Exception as e:
                logger.debug(f"Erreur lors de l'énumération de la fenêtre {hwnd}: {e}")
            
            return True
        
        try:
            win32gui.EnumWindows(enum_windows_callback, None)
        except Exception as e:
            logger.error(f"Erreur énumération fenêtres: {e}")
        
        return windows
    
    def get_active_window(self) -> Optional[WindowInfo]:
        """Récupère la fenêtre active"""
        if not self.enabled:
            return None
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                windows = self.get_all_windows()
                for window in windows:
                    if window.hwnd == hwnd:
                        return window
        except Exception as e:
            logger.error(f"Erreur récupération fenêtre active: {e}")
        
        return None
    
    def activate_window(self, hwnd: int) -> bool:
        """Active une fenêtre par son handle"""
        if not self.enabled:
            return False
        
        try:
            win32gui.SetForegroundWindow(hwnd)
            return True
        except Exception as e:
            logger.error(f"Erreur activation fenêtre {hwnd}: {e}")
            return False
    
    def minimize_window(self, hwnd: int) -> bool:
        """Minimise une fenêtre"""
        if not self.enabled:
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception as e:
            logger.error(f"Erreur minimisation fenêtre {hwnd}: {e}")
            return False
    
    def maximize_window(self, hwnd: int) -> bool:
        """Maximise une fenêtre"""
        if not self.enabled:
            return False
        
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return True
        except Exception as e:
            logger.error(f"Erreur maximisation fenêtre {hwnd}: {e}")
            return False

class CrossPlatformAppDetector:
    """Détecteur d'applications cross-platform utilisant psutil"""
    
    def get_running_processes(self) -> List[ApplicationInfo]:
        """Récupère tous les processus en cours"""
        applications = []
        
        for process in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'memory_info', 'cpu_percent', 'create_time']):
            try:
                info = process.info
                
                # Filtrer les processus système sans interface
                if not info['name'] or info['name'].endswith('.exe') == False:
                    continue
                
                # Calculer l'usage mémoire en MB
                memory_mb = info['memory_info'].rss // (1024 * 1024) if info['memory_info'] else 0
                
                # Ignorer les processus avec très peu de mémoire (probablement des services)
                if memory_mb < 1:
                    continue
                
                app_info = ApplicationInfo(
                    process_id=info['pid'],
                    name=info['name'] or "Unknown",
                    executable_path=info['exe'] or "",
                    command_line=' '.join(info['cmdline']) if info['cmdline'] else "",
                    memory_usage=memory_mb,
                    cpu_percent=info['cpu_percent'] or 0.0,
                    create_time=info['create_time'] or 0.0,
                    windows=[]  # Sera rempli par le détecteur Windows si disponible
                )
                
                applications.append(app_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Erreur traitement processus: {e}")
                continue
        
        return applications

class AppDetector:
    """Détecteur d'applications principal"""
    
    def __init__(self):
        self.windows_detector = WindowsAppDetector()
        self.cross_platform_detector = CrossPlatformAppDetector()
        self.cache: Dict[str, Any] = {}
        self.cache_timeout = 2.0  # Cache de 2 secondes
        self.last_update = 0.0
        
        logger.info("🔍 Détecteur d'applications initialisé")
    
    async def initialize(self):
        """Initialise le détecteur"""
        try:
            # Test de fonctionnement
            await self.get_running_applications()
            logger.success("✅ Détecteur d'applications prêt")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation détecteur: {e}")
            raise
    
    async def get_running_applications(self, use_cache: bool = True) -> List[ApplicationInfo]:
        """Récupère toutes les applications en cours"""
        current_time = time.time()
        
        # Vérifier le cache
        if (use_cache and 
            'applications' in self.cache and 
            current_time - self.last_update < self.cache_timeout):
            return self.cache['applications']
        
        try:
            # Récupérer les processus
            applications = self.cross_platform_detector.get_running_processes()
            
            # Enrichir avec les informations de fenêtres Windows si disponible
            if self.windows_detector.enabled:
                windows = self.windows_detector.get_all_windows()
                
                # Associer les fenêtres aux applications
                for app in applications:
                    app.windows = [w for w in windows if w.process_id == app.process_id]
                    
                    # Marquer comme active si une fenêtre est active
                    app.is_active = any(w.is_active for w in app.windows)
            
            # Trier par usage mémoire décroissant
            applications.sort(key=lambda x: x.memory_usage, reverse=True)
            
            # Mettre en cache
            self.cache['applications'] = applications
            self.last_update = current_time
            
            return applications
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération applications: {e}")
            return []
    
    async def get_active_application(self) -> Optional[ApplicationInfo]:
        """Récupère l'application active"""
        try:
            active_window = self.windows_detector.get_active_window()
            if not active_window:
                return None
            
            applications = await self.get_running_applications()
            
            for app in applications:
                if app.process_id == active_window.process_id:
                    return app
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération application active: {e}")
            return None
    
    async def find_application_by_name(self, name: str, partial_match: bool = True) -> List[ApplicationInfo]:
        """Trouve des applications par nom"""
        applications = await self.get_running_applications()
        
        name_lower = name.lower()
        matches = []
        
        for app in applications:
            app_name_lower = app.name.lower()
            
            if partial_match:
                if name_lower in app_name_lower or app_name_lower in name_lower:
                    matches.append(app)
            else:
                if app_name_lower == name_lower:
                    matches.append(app)
        
        return matches
    
    async def find_application_by_title(self, title: str, partial_match: bool = True) -> List[ApplicationInfo]:
        """Trouve des applications par titre de fenêtre"""
        applications = await self.get_running_applications()
        
        title_lower = title.lower()
        matches = []
        
        for app in applications:
            for window in app.windows:
                window_title_lower = window.title.lower()
                
                if partial_match:
                    if title_lower in window_title_lower:
                        matches.append(app)
                        break
                else:
                    if window_title_lower == title_lower:
                        matches.append(app)
                        break
        
        return matches
    
    async def activate_application(self, app: ApplicationInfo) -> bool:
        """Active une application"""
        if not app.windows:
            logger.warning(f"Aucune fenêtre trouvée pour {app.name}")
            return False
        
        main_window = app.main_window
        if not main_window:
            logger.warning(f"Aucune fenêtre principale pour {app.name}")
            return False
        
        return self.windows_detector.activate_window(main_window.hwnd)
    
    async def close_application(self, app: ApplicationInfo) -> bool:
        """Ferme une application (avec prudence)"""
        try:
            process = psutil.Process(app.process_id)
            
            # Tentative de fermeture propre
            process.terminate()
            
            # Attendre un peu
            await asyncio.sleep(1.0)
            
            # Vérifier si le processus est toujours là
            if process.is_running():
                logger.warning(f"Processus {app.name} toujours actif après terminate")
                # Force kill en dernier recours
                process.kill()
                await asyncio.sleep(0.5)
            
            logger.info(f"✅ Application {app.name} fermée")
            return True
            
        except psutil.NoSuchProcess:
            # Déjà fermé
            return True
        except psutil.AccessDenied:
            logger.error(f"❌ Accès refusé pour fermer {app.name}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur fermeture {app.name}: {e}")
            return False
    
    async def launch_application(self, executable_path: str, args: List[str] = None) -> bool:
        """Lance une application"""
        args = args or []
        
        try:
            command = [executable_path] + args
            process = subprocess.Popen(command, 
                                     stdout=subprocess.DEVNULL, 
                                     stderr=subprocess.DEVNULL)
            
            logger.info(f"✅ Application lancée: {executable_path}")
            return True
            
        except FileNotFoundError:
            logger.error(f"❌ Exécutable non trouvé: {executable_path}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur lancement application: {e}")
            return False
    
    def get_application_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les applications"""
        try:
            applications = self.cache.get('applications', [])
            
            if not applications:
                return {"error": "Aucune donnée disponible"}
            
            total_memory = sum(app.memory_usage for app in applications)
            active_count = sum(1 for app in applications if app.is_active)
            
            stats = {
                "total_applications": len(applications),
                "active_applications": active_count,
                "total_memory_mb": total_memory,
                "top_memory_consumers": [
                    {"name": app.name, "memory_mb": app.memory_usage}
                    for app in applications[:5]
                ],
                "detection_enabled": {
                    "windows": self.windows_detector.enabled,
                    "cross_platform": True
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur calcul statistiques: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """Efface le cache"""
        self.cache.clear()
        self.last_update = 0.0
        logger.debug("🗑️  Cache détecteur applications effacé")

# Fonctions utilitaires
async def get_current_app() -> Optional[ApplicationInfo]:
    """Récupère l'application actuellement active"""
    detector = AppDetector()
    await detector.initialize()
    return await detector.get_active_application()

async def find_app(name: str) -> List[ApplicationInfo]:
    """Trouve une application par nom"""
    detector = AppDetector()
    await detector.initialize()
    return await detector.find_application_by_name(name)

async def switch_to_app(app_name: str) -> bool:
    """Bascule vers une application"""
    detector = AppDetector()
    await detector.initialize()
    
    apps = await detector.find_application_by_name(app_name)
    if apps:
        return await detector.activate_application(apps[0])
    
    logger.warning(f"Application '{app_name}' non trouvée")
    return False

if __name__ == "__main__":
    async def test_app_detector():
        detector = AppDetector()
        await detector.initialize()
        
        # Test récupération applications
        print("🔍 Applications en cours:")
        apps = await detector.get_running_applications()
        
        for i, app in enumerate(apps[:10]):  # Top 10
            status = "🟢 ACTIVE" if app.is_active else "⚪"
            print(f"{status} {app.name} - {app.memory_usage}MB - {len(app.windows)} fenêtres")
        
        # Test application active
        print("\n📱 Application active:")
        active_app = await detector.get_active_application()
        if active_app:
            print(f"- {active_app.name}")
            if active_app.main_window:
                print(f"- Fenêtre: {active_app.main_window.title}")
        
        # Statistiques
        print("\n📊 Statistiques:")
        stats = detector.get_application_stats()
        print(f"- Total: {stats.get('total_applications', 0)} applications")
        print(f"- Actives: {stats.get('active_applications', 0)}")
        print(f"- Mémoire totale: {stats.get('total_memory_mb', 0)}MB")
    
    asyncio.run(test_app_detector())