"""
🛠️ JARVIS Tools - Base Tool Class
Classe de base pour tous les outils JARVIS
"""
import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger

class ToolCategory(Enum):
    """Catégories d'outils"""
    SYSTEM = "system"
    FILE = "file"
    WEB = "web"
    MEDIA = "media"
    AI = "ai"
    AUTOMATION = "automation"
    DEVELOPMENT = "development"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    SECURITY = "security"

class ToolStatus(Enum):
    """États d'exécution d'un outil"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ToolParameter:
    """Paramètre d'un outil"""
    name: str
    type: str  # str, int, float, bool, list, dict, file, url
    description: str
    required: bool = True
    default: Any = None
    choices: Optional[List[Any]] = None
    validation: Optional[Callable] = None

@dataclass
class ToolResult:
    """Résultat d'exécution d'un outil"""
    success: bool
    data: Any = None
    message: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolExecution:
    """Contexte d'exécution d'un outil"""
    id: str
    tool_name: str
    parameters: Dict[str, Any]
    status: ToolStatus
    start_time: float
    end_time: Optional[float] = None
    result: Optional[ToolResult] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None

class BaseTool(ABC):
    """Classe de base pour tous les outils JARVIS"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.id = str(uuid.uuid4())
        self.version = "1.0.0"
        self.enabled = True
        self.execution_count = 0
        self.last_execution = None
        
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Nom d'affichage de l'outil"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description de l'outil"""
        pass
    
    @property
    @abstractmethod
    def category(self) -> ToolCategory:
        """Catégorie de l'outil"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[ToolParameter]:
        """Paramètres requis par l'outil"""
        pass
    
    @property
    def keywords(self) -> List[str]:
        """Mots-clés pour la recherche sémantique"""
        return [self.display_name.lower(), self.description.lower()]
    
    @property
    def dependencies(self) -> List[str]:
        """Dépendances Python requises"""
        return []
    
    @property
    def permissions(self) -> List[str]:
        """Permissions requises (file_read, file_write, network, system, etc.)"""
        return []
    
    @abstractmethod
    async def execute(self, **parameters) -> ToolResult:
        """
        Exécute l'outil avec les paramètres donnés
        
        Args:
            **parameters: Paramètres d'exécution
            
        Returns:
            ToolResult: Résultat de l'exécution
        """
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide et normalise les paramètres
        
        Args:
            parameters: Paramètres à valider
            
        Returns:
            Dict[str, Any]: Paramètres validés
            
        Raises:
            ValueError: Si les paramètres sont invalides
        """
        validated = {}
        
        # Vérifier les paramètres requis
        required_params = [p for p in self.parameters if p.required]
        for param in required_params:
            if param.name not in parameters:
                if param.default is not None:
                    validated[param.name] = param.default
                else:
                    raise ValueError(f"Paramètre requis manquant: {param.name}")
            else:
                validated[param.name] = parameters[param.name]
        
        # Ajouter les paramètres optionnels
        optional_params = [p for p in self.parameters if not p.required]
        for param in optional_params:
            if param.name in parameters:
                validated[param.name] = parameters[param.name]
            elif param.default is not None:
                validated[param.name] = param.default
        
        # Valider les types et contraintes
        for param in self.parameters:
            if param.name in validated:
                value = validated[param.name]
                
                # Validation de type basique
                if param.type == "int" and not isinstance(value, int):
                    try:
                        validated[param.name] = int(value)
                    except ValueError:
                        raise ValueError(f"Paramètre {param.name} doit être un entier")
                
                elif param.type == "float" and not isinstance(value, (int, float)):
                    try:
                        validated[param.name] = float(value)
                    except ValueError:
                        raise ValueError(f"Paramètre {param.name} doit être un nombre")
                
                elif param.type == "bool" and not isinstance(value, bool):
                    if isinstance(value, str):
                        validated[param.name] = value.lower() in ("true", "1", "yes", "on")
                    else:
                        validated[param.name] = bool(value)
                
                # Validation des choix
                if param.choices and value not in param.choices:
                    raise ValueError(f"Paramètre {param.name} doit être dans: {param.choices}")
                
                # Validation personnalisée
                if param.validation:
                    if not param.validation(value):
                        raise ValueError(f"Validation échouée pour le paramètre {param.name}")
        
        return validated
    
    async def safe_execute(self, **parameters) -> ToolResult:
        """
        Exécute l'outil de manière sécurisée avec gestion d'erreurs
        
        Args:
            **parameters: Paramètres d'exécution
            
        Returns:
            ToolResult: Résultat de l'exécution
        """
        execution_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Validation des paramètres
            validated_params = self.validate_parameters(parameters)
            
            logger.info(f"🛠️ Exécution de l'outil {self.display_name} (ID: {execution_id})")
            logger.debug(f"Paramètres: {validated_params}")
            
            # Exécution de l'outil
            result = await self.execute(**validated_params)
            
            # Calcul du temps d'exécution
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # Mise à jour des statistiques
            self.execution_count += 1
            self.last_execution = time.time()
            
            if result.success:
                logger.success(f"✅ Outil {self.display_name} exécuté avec succès en {execution_time:.2f}s")
            else:
                logger.warning(f"⚠️ Outil {self.display_name} terminé avec des erreurs: {result.error}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"❌ Erreur lors de l'exécution de l'outil {self.display_name}: {error_msg}")
            
            return ToolResult(
                success=False,
                error=error_msg,
                execution_time=execution_time,
                message=f"Erreur d'exécution: {error_msg}"
            )
    
    def check_dependencies(self) -> Dict[str, bool]:
        """
        Vérifie si les dépendances sont disponibles
        
        Returns:
            Dict[str, bool]: État des dépendances
        """
        dependency_status = {}
        
        for dep in self.dependencies:
            try:
                __import__(dep)
                dependency_status[dep] = True
            except ImportError:
                dependency_status[dep] = False
        
        return dependency_status
    
    def is_available(self) -> bool:
        """
        Vérifie si l'outil est disponible pour utilisation
        
        Returns:
            bool: True si l'outil est disponible
        """
        if not self.enabled:
            return False
        
        # Vérifier les dépendances
        deps = self.check_dependencies()
        if not all(deps.values()):
            return False
        
        return True
    
    def get_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur l'outil
        
        Returns:
            Dict[str, Any]: Informations de l'outil
        """
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "version": self.version,
            "enabled": self.enabled,
            "available": self.is_available(),
            "execution_count": self.execution_count,
            "last_execution": self.last_execution,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "choices": p.choices
                }
                for p in self.parameters
            ],
            "keywords": self.keywords,
            "dependencies": self.dependencies,
            "permissions": self.permissions
        }
    
    def __str__(self) -> str:
        return f"{self.display_name} ({self.category.value})"
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.display_name}>"