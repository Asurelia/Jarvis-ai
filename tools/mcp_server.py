"""
🔌 JARVIS MCP Server
Serveur Model Context Protocol pour l'intégration avec les LLMs
"""
import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from loguru import logger

from .tool_manager import tool_manager
from .base_tool import ToolResult

class MCPRequestType(Enum):
    """Types de requêtes MCP"""
    LIST_TOOLS = "tools/list"
    CALL_TOOL = "tools/call"
    GET_TOOL_INFO = "tools/info"
    SEARCH_TOOLS = "tools/search"

@dataclass
class MCPRequest:
    """Requête MCP"""
    id: str
    method: str
    params: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class MCPResponse:
    """Réponse MCP"""
    id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

@dataclass
class MCPToolDefinition:
    """Définition d'outil pour MCP"""
    name: str
    description: str
    inputSchema: Dict[str, Any]
    
    @classmethod
    def from_jarvis_tool(cls, tool):
        """Convertit un outil JARVIS en définition MCP"""
        properties = {}
        required = []
        
        for param in tool.parameters:
            param_schema = {
                "type": cls._convert_type(param.type),
                "description": param.description
            }
            
            if param.choices:
                param_schema["enum"] = param.choices
            
            if param.default is not None:
                param_schema["default"] = param.default
            
            properties[param.name] = param_schema
            
            if param.required:
                required.append(param.name)
        
        input_schema = {
            "type": "object",
            "properties": properties
        }
        
        if required:
            input_schema["required"] = required
        
        return cls(
            name=tool.name,
            description=f"{tool.display_name}: {tool.description}",
            inputSchema=input_schema
        )
    
    @staticmethod
    def _convert_type(jarvis_type: str) -> str:
        """Convertit les types JARVIS vers les types JSON Schema"""
        type_mapping = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object",
            "file": "string",
            "url": "string"
        }
        return type_mapping.get(jarvis_type, "string")

class MCPServer:
    """Serveur MCP pour JARVIS"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.server = None
        self.clients = set()
        
        # Configuration MCP
        self.server_info = {
            "name": "jarvis-mcp-server",
            "version": "1.0.0",
            "description": "JARVIS Model Context Protocol Server",
            "capabilities": {
                "tools": {
                    "listChanged": True,
                    "supportsProgress": True
                }
            }
        }
        
        # Statistiques
        self.stats = {
            "requests_handled": 0,
            "tools_called": 0,
            "connected_clients": 0,
            "start_time": time.time()
        }
        
        logger.info(f"🔌 Serveur MCP JARVIS initialisé ({host}:{port})")
    
    async def start(self):
        """Démarre le serveur MCP"""
        try:
            import websockets
            
            logger.info(f"🚀 Démarrage du serveur MCP sur {self.host}:{self.port}")
            
            self.server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )
            
            logger.success(f"✅ Serveur MCP démarré sur ws://{self.host}:{self.port}")
            
            # Attendre indéfiniment
            await self.server.wait_closed()
            
        except ImportError:
            logger.error("❌ Module websockets requis: pip install websockets")
        except Exception as e:
            logger.error(f"❌ Erreur démarrage serveur MCP: {e}")
    
    async def stop(self):
        """Arrête le serveur MCP"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("🛑 Serveur MCP arrêté")
    
    async def handle_client(self, websocket, path):
        """Gère une connexion client"""
        client_id = str(uuid.uuid4())
        self.clients.add(websocket)
        self.stats["connected_clients"] += 1
        
        logger.info(f"🔗 Nouveau client MCP connecté: {client_id}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
                
        except Exception as e:
            logger.error(f"❌ Erreur client MCP {client_id}: {e}")
        finally:
            self.clients.remove(websocket)
            self.stats["connected_clients"] -= 1
            logger.info(f"🔌 Client MCP déconnecté: {client_id}")
    
    async def process_message(self, websocket, message: str):
        """Traite un message MCP"""
        try:
            # Parser le message JSON
            data = json.loads(message)
            
            # Créer la requête MCP
            request = MCPRequest(
                id=data.get("id", str(uuid.uuid4())),
                method=data.get("method", ""),
                params=data.get("params", {})
            )
            
            self.stats["requests_handled"] += 1
            
            # Router la requête
            response = await self.route_request(request)
            
            # Envoyer la réponse
            response_json = json.dumps(asdict(response))
            await websocket.send(response_json)
            
        except json.JSONDecodeError as e:
            # Réponse d'erreur pour JSON invalide
            error_response = MCPResponse(
                id="unknown",
                error={
                    "code": -32700,
                    "message": "Parse error",
                    "data": str(e)
                }
            )
            await websocket.send(json.dumps(asdict(error_response)))
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement message MCP: {e}")
            error_response = MCPResponse(
                id=data.get("id", "unknown") if 'data' in locals() else "unknown",
                error={
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            )
            await websocket.send(json.dumps(asdict(error_response)))
    
    async def route_request(self, request: MCPRequest) -> MCPResponse:
        """Route une requête vers le bon handler"""
        method = request.method
        
        if method == "initialize":
            return await self.handle_initialize(request)
        elif method == "tools/list":
            return await self.handle_list_tools(request)
        elif method == "tools/call":
            return await self.handle_call_tool(request)
        elif method == "tools/info":
            return await self.handle_get_tool_info(request)
        elif method == "tools/search":
            return await self.handle_search_tools(request)
        else:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32601,
                    "message": "Method not found",
                    "data": f"Unknown method: {method}"
                }
            )
    
    async def handle_initialize(self, request: MCPRequest) -> MCPResponse:
        """Gère l'initialisation MCP"""
        return MCPResponse(
            id=request.id,
            result={
                "protocolVersion": "1.0.0",
                "serverInfo": self.server_info,
                "capabilities": self.server_info["capabilities"]
            }
        )
    
    async def handle_list_tools(self, request: MCPRequest) -> MCPResponse:
        """Liste tous les outils disponibles"""
        try:
            # Récupérer tous les outils
            tools_info = tool_manager.list_tools()
            
            # Convertir en format MCP
            mcp_tools = []
            for tool_info in tools_info:
                # Récupérer l'instance de l'outil
                tool = tool_manager.get_tool(tool_info["name"])
                if tool:
                    mcp_tool = MCPToolDefinition.from_jarvis_tool(tool)
                    mcp_tools.append(asdict(mcp_tool))
            
            return MCPResponse(
                id=request.id,
                result={
                    "tools": mcp_tools
                }
            )
            
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Error listing tools",
                    "data": str(e)
                }
            )
    
    async def handle_call_tool(self, request: MCPRequest) -> MCPResponse:
        """Exécute un outil"""
        try:
            params = request.params
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid params",
                        "data": "Tool name is required"
                    }
                )
            
            # Exécuter l'outil
            result = await tool_manager.execute_tool(tool_name, arguments)
            self.stats["tools_called"] += 1
            
            # Formater la réponse MCP
            if result.success:
                response_content = {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result.data) if result.data is not None else result.message
                        }
                    ],
                    "isError": False
                }
                
                # Ajouter les métadonnées si disponibles
                if result.metadata:
                    response_content["metadata"] = result.metadata
                
            else:
                response_content = {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {result.error or result.message}"
                        }
                    ],
                    "isError": True
                }
            
            return MCPResponse(
                id=request.id,
                result=response_content
            )
            
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Error calling tool",
                    "data": str(e)
                }
            )
    
    async def handle_get_tool_info(self, request: MCPRequest) -> MCPResponse:
        """Récupère les informations d'un outil spécifique"""
        try:
            params = request.params
            tool_name = params.get("name")
            
            if not tool_name:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid params",
                        "data": "Tool name is required"
                    }
                )
            
            tool = tool_manager.get_tool(tool_name)
            if not tool:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Tool not found",
                        "data": f"Tool '{tool_name}' does not exist"
                    }
                )
            
            tool_info = tool.get_info()
            mcp_tool = MCPToolDefinition.from_jarvis_tool(tool)
            
            return MCPResponse(
                id=request.id,
                result={
                    "tool": asdict(mcp_tool),
                    "info": tool_info
                }
            )
            
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Error getting tool info",
                    "data": str(e)
                }
            )
    
    async def handle_search_tools(self, request: MCPRequest) -> MCPResponse:
        """Recherche d'outils par requête"""
        try:
            params = request.params
            query = params.get("query", "")
            max_results = params.get("max_results", 5)
            
            if not query:
                return MCPResponse(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Invalid params",
                        "data": "Search query is required"
                    }
                )
            
            # Rechercher les outils
            matches = tool_manager.search_tools(query, max_results)
            
            # Convertir en format MCP
            mcp_matches = []
            for match in matches:
                tool_info = match["tool"]
                similarity = match["similarity"]
                
                tool = tool_manager.get_tool(tool_info["name"])
                if tool:
                    mcp_tool = MCPToolDefinition.from_jarvis_tool(tool)
                    mcp_matches.append({
                        "tool": asdict(mcp_tool),
                        "similarity": similarity,
                        "info": tool_info
                    })
            
            return MCPResponse(
                id=request.id,
                result={
                    "matches": mcp_matches,
                    "query": query
                }
            )
            
        except Exception as e:
            return MCPResponse(
                id=request.id,
                error={
                    "code": -32603,
                    "message": "Error searching tools",
                    "data": str(e)
                }
            )
    
    async def broadcast_tool_list_changed(self):
        """Diffuse une notification de changement de liste d'outils"""
        if not self.clients:
            return
        
        notification = {
            "method": "notifications/tools/listChanged",
            "params": {}
        }
        
        message = json.dumps(notification)
        
        # Envoyer à tous les clients connectés
        disconnected_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception:
                disconnected_clients.add(client)
        
        # Nettoyer les clients déconnectés
        self.clients -= disconnected_clients
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du serveur MCP"""
        return {
            **self.stats,
            "uptime": time.time() - self.stats["start_time"],
            "tools_available": len(tool_manager.registry.tools)
        }

# Instance globale du serveur MCP
mcp_server = MCPServer()