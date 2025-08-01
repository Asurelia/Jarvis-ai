"""
🛑 Graceful Shutdown Manager
Gestion propre de l'arrêt des services avec cleanup des ressources et drain des requêtes
"""

import asyncio
import logging
import signal
import sys
import time
from typing import Any, Callable, Dict, List, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ShutdownState(Enum):
    RUNNING = "running"
    DRAINING = "draining"
    SHUTTING_DOWN = "shutting_down"
    STOPPED = "stopped"

@dataclass
class ShutdownHook:
    """Hook d'arrêt avec priorité et timeout"""
    name: str
    callback: Callable
    priority: int = 50  # Plus bas = exécuté en premier
    timeout: float = 30.0
    executed: bool = False
    execution_time: Optional[float] = None
    error: Optional[Exception] = None

class GracefulShutdownManager:
    """
    Gestionnaire d'arrêt propre avec:
    - Gestion des signaux SIGTERM/SIGINT
    - Drain des requêtes en cours
    - Exécution ordonnée des hooks de cleanup
    - Timeout configurable pour chaque étape
    - Monitoring du processus d'arrêt
    """
    
    def __init__(
        self,
        service_name: str,
        drain_timeout: float = 30.0,
        shutdown_timeout: float = 60.0,
        force_exit_timeout: float = 90.0
    ):
        self.service_name = service_name
        self.drain_timeout = drain_timeout
        self.shutdown_timeout = shutdown_timeout
        self.force_exit_timeout = force_exit_timeout
        
        self.state = ShutdownState.RUNNING
        self.shutdown_hooks: List[ShutdownHook] = []
        self.active_requests = 0
        self.shutdown_started_at: Optional[float] = None
        self.shutdown_completed_at: Optional[float] = None
        
        # Event pour signaler l'arrêt
        self.shutdown_event = asyncio.Event()
        self.drain_complete_event = asyncio.Event()
        
        # Statistiques
        self.stats = {
            "total_hooks": 0,
            "successful_hooks": 0,
            "failed_hooks": 0,
            "total_shutdown_time": 0.0,
            "requests_drained": 0,
            "forced_exit": False
        }
        
        self._signal_handlers_installed = False
        self._original_handlers = {}
        
        logger.info(f"🛑 Graceful Shutdown Manager initialisé pour '{service_name}'")
    
    def install_signal_handlers(self):
        """Installer les gestionnaires de signaux"""
        if self._signal_handlers_installed:
            return
        
        # Sauvegarder les handlers originaux
        for sig in [signal.SIGTERM, signal.SIGINT]:
            try:
                self._original_handlers[sig] = signal.signal(sig, self._signal_handler)
            except (OSError, ValueError) as e:
                logger.warning(f"⚠️ Impossible d'installer handler pour {sig}: {e}")
        
        # Handler spécial pour SIGQUIT (dump état)
        try:
            signal.signal(signal.SIGQUIT, self._dump_state_handler)
        except (OSError, ValueError):
            pass  # SIGQUIT pas disponible sur tous les systèmes
        
        self._signal_handlers_installed = True
        logger.info("📶 Signal handlers installés (SIGTERM, SIGINT)")
    
    def _signal_handler(self, signum: int, frame):
        """Gestionnaire de signal pour déclenchement arrêt"""
        signal_name = signal.Signals(signum).name
        logger.info(f"📶 Signal {signal_name} reçu, démarrage arrêt gracieux...")
        
        # Démarrer l'arrêt dans la boucle d'événements
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.shutdown())
        except RuntimeError:
            # Pas de loop en cours, arrêt brutal
            logger.error("❌ Pas de boucle d'événements, arrêt brutal")
            sys.exit(1)
    
    def _dump_state_handler(self, signum: int, frame):
        """Dump l'état actuel du service (SIGQUIT)"""
        logger.info("📊 Dump état du service (SIGQUIT):")
        state_info = self.get_state_info()
        for key, value in state_info.items():
            logger.info(f"  {key}: {value}")
    
    def add_shutdown_hook(
        self,
        name: str,
        callback: Callable,
        priority: int = 50,
        timeout: float = 30.0
    ):
        """
        Ajouter un hook d'arrêt
        
        Args:
            name: Nom du hook
            callback: Fonction à appeler (sync ou async)
            priority: Priorité (plus bas = exécuté en premier)
            timeout: Timeout pour l'exécution
        """
        hook = ShutdownHook(
            name=name,
            callback=callback,
            priority=priority,
            timeout=timeout
        )
        
        self.shutdown_hooks.append(hook)
        self.shutdown_hooks.sort(key=lambda h: h.priority)
        self.stats["total_hooks"] += 1
        
        logger.info(f"🔗 Hook d'arrêt ajouté: '{name}' (priorité: {priority})")
    
    def remove_shutdown_hook(self, name: str) -> bool:
        """Supprimer un hook d'arrêt"""
        for i, hook in enumerate(self.shutdown_hooks):
            if hook.name == name:
                del self.shutdown_hooks[i]
                self.stats["total_hooks"] -= 1
                logger.info(f"🗑️ Hook d'arrêt supprimé: '{name}'")
                return True
        return False
    
    @asynccontextmanager
    async def request_context(self):
        """Context manager pour tracker les requêtes actives"""
        self.active_requests += 1
        try:
            yield
        finally:
            self.active_requests -= 1
            if self.state == ShutdownState.DRAINING and self.active_requests == 0:
                self.drain_complete_event.set()
    
    async def wait_for_shutdown(self):
        """Attendre le signal d'arrêt"""
        await self.shutdown_event.wait()
    
    async def shutdown(self):
        """Démarrer le processus d'arrêt gracieux"""
        if self.state != ShutdownState.RUNNING:
            logger.warning("⚠️ Arrêt déjà en cours")
            return
        
        self.shutdown_started_at = time.time()
        logger.info(f"🛑 Démarrage arrêt gracieux de '{self.service_name}'")
        
        try:
            # Étape 1: Drain des requêtes
            await self._drain_requests()
            
            # Étape 2: Exécution des hooks
            await self._execute_shutdown_hooks()
            
            # Étape 3: Arrêt complet
            self.state = ShutdownState.STOPPED
            self.shutdown_completed_at = time.time()
            self.stats["total_shutdown_time"] = self.shutdown_completed_at - self.shutdown_started_at
            
            logger.info(f"✅ Arrêt gracieux terminé en {self.stats['total_shutdown_time']:.2f}s")
            
        except Exception as e:
            logger.error(f"❌ Erreur pendant arrêt gracieux: {e}")
            self.stats["forced_exit"] = True
        
        finally:
            self.shutdown_event.set()
            
            # Forcer l'arrêt après timeout si nécessaire
            asyncio.create_task(self._force_exit_after_timeout())
    
    async def _drain_requests(self):
        """Drainer les requêtes en cours"""
        if self.active_requests == 0:
            logger.info("✅ Aucune requête active à drainer")
            return
        
        self.state = ShutdownState.DRAINING
        logger.info(f"🚰 Drain de {self.active_requests} requêtes actives...")
        
        try:
            # Attendre que toutes les requêtes se terminent ou timeout
            await asyncio.wait_for(
                self.drain_complete_event.wait(),
                timeout=self.drain_timeout
            )
            
            self.stats["requests_drained"] = self.active_requests
            logger.info(f"✅ Drain terminé - {self.stats['requests_drained']} requêtes")
            
        except asyncio.TimeoutError:
            logger.warning(
                f"⚠️ Timeout drain ({self.drain_timeout}s) - "
                f"{self.active_requests} requêtes encore actives"
            )
    
    async def _execute_shutdown_hooks(self):
        """Exécuter tous les hooks d'arrêt dans l'ordre de priorité"""
        if not self.shutdown_hooks:
            logger.info("✅ Aucun hook d'arrêt à exécuter")
            return
        
        self.state = ShutdownState.SHUTTING_DOWN
        logger.info(f"🔗 Exécution de {len(self.shutdown_hooks)} hooks d'arrêt...")
        
        for hook in self.shutdown_hooks:
            if hook.executed:
                continue
            
            start_time = time.time()
            
            try:
                logger.info(f"🔗 Exécution hook: '{hook.name}'")
                
                # Exécuter avec timeout
                if asyncio.iscoroutinefunction(hook.callback):
                    await asyncio.wait_for(hook.callback(), timeout=hook.timeout)
                else:
                    # Exécuter fonction sync dans thread pool
                    loop = asyncio.get_running_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(None, hook.callback),
                        timeout=hook.timeout
                    )
                
                hook.execution_time = time.time() - start_time
                hook.executed = True
                self.stats["successful_hooks"] += 1
                
                logger.info(f"✅ Hook '{hook.name}' terminé en {hook.execution_time:.2f}s")
                
            except asyncio.TimeoutError:
                hook.error = f"Timeout ({hook.timeout}s)"
                hook.executed = True
                self.stats["failed_hooks"] += 1
                logger.error(f"❌ Hook '{hook.name}' timeout après {hook.timeout}s")
                
            except Exception as e:
                hook.error = e
                hook.executed = True
                self.stats["failed_hooks"] += 1
                logger.error(f"❌ Hook '{hook.name}' échoué: {e}")
        
        success_rate = (self.stats["successful_hooks"] / len(self.shutdown_hooks)) * 100
        logger.info(f"📊 Hooks terminés: {success_rate:.1f}% succès")
    
    async def _force_exit_after_timeout(self):
        """Forcer l'arrêt après timeout ultime"""
        await asyncio.sleep(self.force_exit_timeout)
        
        if self.state != ShutdownState.STOPPED:
            logger.error(
                f"💥 Arrêt forcé après {self.force_exit_timeout}s - "
                f"État: {self.state.value}"
            )
            self.stats["forced_exit"] = True
            sys.exit(1)
    
    def get_state_info(self) -> Dict[str, Any]:
        """Obtenir informations d'état détaillées"""
        uptime = None
        shutdown_duration = None
        
        if self.shutdown_started_at:
            shutdown_duration = time.time() - self.shutdown_started_at
        
        return {
            "service_name": self.service_name,
            "state": self.state.value,
            "active_requests": self.active_requests,
            "shutdown_started_at": self.shutdown_started_at,
            "shutdown_duration": shutdown_duration,
            "hooks_total": len(self.shutdown_hooks),
            "hooks_executed": sum(1 for h in self.shutdown_hooks if h.executed),
            "stats": self.stats
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtenir statistiques d'arrêt"""
        return {
            **self.stats,
            "state": self.state.value,
            "active_requests": self.active_requests
        }

# Factory function pour création rapide
def create_shutdown_manager(
    service_name: str,
    **kwargs
) -> GracefulShutdownManager:
    """Créer et configurer un gestionnaire d'arrêt"""
    manager = GracefulShutdownManager(service_name, **kwargs)
    manager.install_signal_handlers()
    return manager

# Décorateur pour fonctions de cleanup
def shutdown_hook(name: str, priority: int = 50, timeout: float = 30.0):
    """
    Décorateur pour enregistrer automatiquement une fonction comme hook d'arrêt
    
    Usage:
        @shutdown_hook("cleanup_database", priority=10)
        async def cleanup_db():
            pass
    """
    def decorator(func):
        # Enregistrement différé - nécessite instance de manager
        func._shutdown_hook_config = {
            "name": name,
            "priority": priority,
            "timeout": timeout
        }
        return func
    return decorator

# Context manager pour requêtes avec shutdown
@asynccontextmanager
async def request_lifecycle(shutdown_manager: GracefulShutdownManager):
    """Context manager pour lifecycle complet d'une requête"""
    if shutdown_manager.state != ShutdownState.RUNNING:
        raise RuntimeError("Service en cours d'arrêt")
    
    async with shutdown_manager.request_context():
        yield

# Utilitaires pour intégration FastAPI
class ShutdownMiddleware:
    """Middleware FastAPI pour integration graceful shutdown"""
    
    def __init__(self, app, shutdown_manager: GracefulShutdownManager):
        self.app = app
        self.shutdown_manager = shutdown_manager
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        
        # Vérifier si service en cours d'arrêt
        if self.shutdown_manager.state != ShutdownState.RUNNING:
            response = {
                "type": "http.response.start",
                "status": 503,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"retry-after", b"30")
                ]
            }
            await send(response)
            
            body = {
                "type": "http.response.body",
                "body": b'{"error":"Service unavailable - shutting down"}'
            }
            await send(body)
            return
        
        # Traiter requête avec tracking
        async with self.shutdown_manager.request_context():
            await self.app(scope, receive, send)

# Configuration prédéfinie pour services JARVIS
JARVIS_SHUTDOWN_CONFIGS = {
    "brain-api": {
        "drain_timeout": 45.0,
        "shutdown_timeout": 90.0,
        "force_exit_timeout": 120.0
    },
    "tts-service": {
        "drain_timeout": 30.0,
        "shutdown_timeout": 60.0,
        "force_exit_timeout": 90.0
    },
    "stt-service": {
        "drain_timeout": 20.0,
        "shutdown_timeout": 45.0,
        "force_exit_timeout": 60.0
    },
    "ollama": {
        "drain_timeout": 60.0,
        "shutdown_timeout": 120.0,
        "force_exit_timeout": 180.0
    },
    "default": {
        "drain_timeout": 30.0,
        "shutdown_timeout": 60.0,
        "force_exit_timeout": 90.0
    }
}

def create_jarvis_shutdown_manager(service_name: str) -> GracefulShutdownManager:
    """Créer gestionnaire d'arrêt avec configuration JARVIS"""
    config = JARVIS_SHUTDOWN_CONFIGS.get(service_name, JARVIS_SHUTDOWN_CONFIGS["default"])
    return create_shutdown_manager(service_name, **config)