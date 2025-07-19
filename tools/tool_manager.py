"""
🛠️ JARVIS Tools - Tool Manager
Gestionnaire principal des outils avec découverte automatique et MCP
"""
import asyncio
import importlib
import inspect
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Union
from dataclasses import dataclass
import json
from loguru import logger

from .base_tool import BaseTool, ToolResult, ToolCategory, ToolExecution, ToolStatus
from sentence_transformers import SentenceTransformer
import numpy as np

@dataclass
class ToolRegistry:
    """Registre des outils disponibles"""
    tools: Dict[str, BaseTool]
    categories: Dict[ToolCategory, List[str]]
    executions: Dict[str, ToolExecution]
    
    def __post_init__(self):
        if not hasattr(self, 'categories'):
            self.categories = {category: [] for category in ToolCategory}

class ToolManager:
    """Gestionnaire principal des outils JARVIS"""
    
    def __init__(self, tools_directory: str = "tools"):
        self.tools_directory = Path(tools_directory)
        self.registry = ToolRegistry(
            tools={},
            categories={category: [] for category in ToolCategory},
            executions={}
        )
        
        # Modèle de similarité sémantique pour la sélection d'outils
        self.similarity_model = None
        self.tool_embeddings = {}
        
        # Configuration
        self.config = {
            "auto_discovery": True,
            "similarity_threshold": 0.7,
            "max_concurrent_executions": 5,
            "execution_timeout": 300,  # 5 minutes
            "enable_mcp": True
        }
        
        # Statistiques
        self.stats = {
            "tools_loaded": 0,
            "tools_executed": 0,
            "executions_successful": 0,
            "executions_failed": 0,
            "total_execution_time": 0.0
        }
        
        logger.info("🛠️ Gestionnaire d'outils JARVIS initialisé")
    
    async def initialize(self):
        """Initialise le gestionnaire d'outils"""
        try:
            logger.info("🚀 Initialisation du gestionnaire d'outils...")
            
            # Initialiser le modèle de similarité
            await self._initialize_similarity_model()
            
            # Découverte automatique des outils
            if self.config["auto_discovery"]:
                await self.discover_tools()
            
            # Charger les outils de base
            await self._load_builtin_tools()
            
            logger.success(f"✅ Gestionnaire d'outils prêt avec {len(self.registry.tools)} outils")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation gestionnaire d'outils: {e}")
            return False
    
    async def _initialize_similarity_model(self):
        """Initialise le modèle de similarité sémantique"""
        try:
            logger.info("🧠 Chargement du modèle de similarité...")
            self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.success("✅ Modèle de similarité chargé")
        except Exception as e:
            logger.warning(f"⚠️ Impossible de charger le modèle de similarité: {e}")
            self.similarity_model = None
    
    async def discover_tools(self):
        """Découvre automatiquement les outils disponibles"""
        discovered_count = 0
        
        # Parcourir le dossier des outils
        tools_path = self.tools_directory
        if not tools_path.exists():
            logger.warning(f"📁 Dossier des outils non trouvé: {tools_path}")
            return
        
        for tool_file in tools_path.glob("*_tool.py"):
            try:
                # Importer le module
                module_name = f"tools.{tool_file.stem}"
                module = importlib.import_module(module_name)
                
                # Chercher les classes qui héritent de BaseTool
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseTool) and 
                        obj != BaseTool and 
                        not obj.__name__.startswith('_')):
                        
                        try:
                            # Instancier l'outil
                            tool = obj()
                            await self.register_tool(tool)
                            discovered_count += 1
                            
                        except Exception as e:
                            logger.error(f"❌ Erreur lors de l'instanciation de {name}: {e}")
                            
            except Exception as e:
                logger.error(f"❌ Erreur lors du chargement de {tool_file}: {e}")
        
        logger.info(f"🔍 {discovered_count} outils découverts automatiquement")
    
    async def _load_builtin_tools(self):
        """Charge les outils intégrés"""
        try:
            # Importer et charger les outils de base
            from .system_tools import (
                FileReadTool, FileWriteTool, DirectoryListTool,
                ProcessListTool, SystemInfoTool
            )
            from .web_tools import WebSearchTool, WebScrapeTool, DownloadTool
            from .ai_tools import TextGenerationTool, ImageAnalysisTool, TranslationTool
            
            builtin_tools = [
                FileReadTool(), FileWriteTool(), DirectoryListTool(),
                ProcessListTool(), SystemInfoTool(),
                WebSearchTool(), WebScrapeTool(), DownloadTool(),
                TextGenerationTool(), ImageAnalysisTool(), TranslationTool()
            ]
            
            for tool in builtin_tools:
                await self.register_tool(tool)
                
            logger.info(f"📦 {len(builtin_tools)} outils intégrés chargés")
            
        except ImportError as e:
            logger.warning(f"⚠️ Certains outils intégrés ne sont pas disponibles: {e}")
    
    async def register_tool(self, tool: BaseTool):
        """
        Enregistre un nouvel outil
        
        Args:
            tool: Instance de l'outil à enregistrer
        """
        try:
            tool_name = tool.name
            
            # Vérifier si l'outil est disponible
            if not tool.is_available():
                logger.warning(f"⚠️ Outil {tool_name} non disponible (dépendances manquantes)")
                return False
            
            # Ajouter au registre
            self.registry.tools[tool_name] = tool
            
            # Ajouter à la catégorie
            category = tool.category
            if tool_name not in self.registry.categories[category]:
                self.registry.categories[category].append(tool_name)
            
            # Générer l'embedding pour la recherche sémantique
            if self.similarity_model:
                text_for_embedding = f"{tool.display_name} {tool.description} {' '.join(tool.keywords)}"
                embedding = self.similarity_model.encode(text_for_embedding)
                self.tool_embeddings[tool_name] = embedding
            
            self.stats["tools_loaded"] += 1
            
            logger.debug(f"🛠️ Outil enregistré: {tool.display_name} ({category.value})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'enregistrement de l'outil {tool.name}: {e}")
            return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        Récupère un outil par son nom
        
        Args:
            tool_name: Nom de l'outil
            
        Returns:
            BaseTool: Instance de l'outil ou None
        """
        return self.registry.tools.get(tool_name)
    
    def list_tools(self, category: Optional[ToolCategory] = None, 
                  available_only: bool = True) -> List[Dict[str, Any]]:
        """
        Liste les outils disponibles
        
        Args:
            category: Filtrer par catégorie (optionnel)
            available_only: Ne lister que les outils disponibles
            
        Returns:
            List[Dict]: Liste des informations des outils
        """
        tools_info = []
        
        for tool_name, tool in self.registry.tools.items():
            if available_only and not tool.is_available():
                continue
            
            if category and tool.category != category:
                continue
            
            tools_info.append(tool.get_info())
        
        return tools_info
    
    def search_tools(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche d'outils par similarité sémantique
        
        Args:
            query: Requête de recherche
            max_results: Nombre maximum de résultats
            
        Returns:
            List[Dict]: Liste des outils trouvés avec scores
        """
        if not self.similarity_model or not self.tool_embeddings:
            # Fallback: recherche par mots-clés
            return self._keyword_search(query, max_results)
        
        try:
            # Générer l'embedding de la requête
            query_embedding = self.similarity_model.encode(query)
            
            # Calculer les similarités
            similarities = []
            for tool_name, tool_embedding in self.tool_embeddings.items():
                similarity = np.dot(query_embedding, tool_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(tool_embedding)
                )
                
                if similarity >= self.config["similarity_threshold"]:
                    tool = self.registry.tools[tool_name]
                    similarities.append({
                        "tool": tool.get_info(),
                        "similarity": float(similarity)
                    })
            
            # Trier par similarité décroissante
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            return similarities[:max_results]
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche sémantique: {e}")
            return self._keyword_search(query, max_results)
    
    def _keyword_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Recherche par mots-clés (fallback)"""
        query_lower = query.lower()
        matches = []
        
        for tool_name, tool in self.registry.tools.items():
            if not tool.is_available():
                continue
            
            score = 0
            
            # Vérifier le nom et la description
            if query_lower in tool.display_name.lower():
                score += 1.0
            if query_lower in tool.description.lower():
                score += 0.8
            
            # Vérifier les mots-clés
            for keyword in tool.keywords:
                if query_lower in keyword:
                    score += 0.6
            
            if score > 0:
                matches.append({
                    "tool": tool.get_info(),
                    "similarity": score
                })
        
        matches.sort(key=lambda x: x["similarity"], reverse=True)
        return matches[:max_results]
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any] = None,
                          user_id: str = None, session_id: str = None) -> ToolResult:
        """
        Exécute un outil
        
        Args:
            tool_name: Nom de l'outil à exécuter
            parameters: Paramètres d'exécution
            user_id: ID de l'utilisateur (optionnel)
            session_id: ID de session (optionnel)
            
        Returns:
            ToolResult: Résultat de l'exécution
        """
        if parameters is None:
            parameters = {}
        
        # Vérifier si l'outil existe
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Outil '{tool_name}' non trouvé",
                message="L'outil demandé n'existe pas"
            )
        
        # Vérifier si l'outil est disponible
        if not tool.is_available():
            return ToolResult(
                success=False,
                error=f"Outil '{tool_name}' non disponible",
                message="L'outil n'est pas disponible (dépendances manquantes)"
            )
        
        # Créer le contexte d'exécution
        execution = ToolExecution(
            id=f"exec_{int(time.time())}_{tool_name}",
            tool_name=tool_name,
            parameters=parameters,
            status=ToolStatus.RUNNING,
            start_time=time.time(),
            user_id=user_id,
            session_id=session_id
        )
        
        # Ajouter au registre des exécutions
        self.registry.executions[execution.id] = execution
        
        try:
            logger.info(f"🚀 Exécution de l'outil: {tool.display_name}")
            
            # Exécuter l'outil
            result = await tool.safe_execute(**parameters)
            
            # Mettre à jour l'exécution
            execution.status = ToolStatus.COMPLETED if result.success else ToolStatus.FAILED
            execution.end_time = time.time()
            execution.result = result
            
            # Mettre à jour les statistiques
            self.stats["tools_executed"] += 1
            self.stats["total_execution_time"] += result.execution_time
            
            if result.success:
                self.stats["executions_successful"] += 1
            else:
                self.stats["executions_failed"] += 1
            
            return result
            
        except Exception as e:
            execution.status = ToolStatus.FAILED
            execution.end_time = time.time()
            
            error_result = ToolResult(
                success=False,
                error=str(e),
                message=f"Erreur lors de l'exécution: {str(e)}"
            )
            execution.result = error_result
            
            self.stats["tools_executed"] += 1
            self.stats["executions_failed"] += 1
            
            return error_result
    
    async def execute_tool_by_query(self, query: str, parameters: Dict[str, Any] = None) -> ToolResult:
        """
        Exécute un outil en trouvant le meilleur match pour une requête
        
        Args:
            query: Requête en langage naturel
            parameters: Paramètres d'exécution
            
        Returns:
            ToolResult: Résultat de l'exécution
        """
        # Rechercher les outils correspondants
        matches = self.search_tools(query, max_results=1)
        
        if not matches:
            return ToolResult(
                success=False,
                error="Aucun outil trouvé",
                message=f"Aucun outil ne correspond à la requête: '{query}'"
            )
        
        # Prendre le meilleur match
        best_match = matches[0]
        tool_name = best_match["tool"]["name"]
        similarity = best_match["similarity"]
        
        logger.info(f"🎯 Outil sélectionné: {tool_name} (similarité: {similarity:.2f})")
        
        # Exécuter l'outil
        return await self.execute_tool(tool_name, parameters)
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des exécutions
        
        Args:
            limit: Nombre maximum d'exécutions à retourner
            
        Returns:
            List[Dict]: Historique des exécutions
        """
        executions = list(self.registry.executions.values())
        executions.sort(key=lambda x: x.start_time, reverse=True)
        
        return [
            {
                "id": exec.id,
                "tool_name": exec.tool_name,
                "status": exec.status.value,
                "start_time": exec.start_time,
                "end_time": exec.end_time,
                "execution_time": (exec.end_time - exec.start_time) if exec.end_time else None,
                "success": exec.result.success if exec.result else None,
                "user_id": exec.user_id,
                "session_id": exec.session_id
            }
            for exec in executions[:limit]
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du gestionnaire"""
        stats = self.stats.copy()
        
        # Ajouter des métriques calculées
        if stats["tools_executed"] > 0:
            stats["success_rate"] = stats["executions_successful"] / stats["tools_executed"]
            stats["avg_execution_time"] = stats["total_execution_time"] / stats["tools_executed"]
        else:
            stats["success_rate"] = 0.0
            stats["avg_execution_time"] = 0.0
        
        stats["tools_available"] = len([t for t in self.registry.tools.values() if t.is_available()])
        stats["categories"] = {cat.value: len(tools) for cat, tools in self.registry.categories.items()}
        
        return stats
    
    def export_tools_manifest(self, filepath: str):
        """Exporte la liste des outils au format JSON"""
        manifest = {
            "version": "1.0.0",
            "generated_at": time.time(),
            "tools": self.list_tools(),
            "categories": {cat.value: tools for cat, tools in self.registry.categories.items()},
            "stats": self.get_stats()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📄 Manifest des outils exporté: {filepath}")

# Instance globale du gestionnaire
tool_manager = ToolManager()