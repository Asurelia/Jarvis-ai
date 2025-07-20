"""
🔧 MCP Gateway - JARVIS 2025
Passerelle Model Context Protocol pour intégration IDE et outils
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
import uvicorn
import asyncio
import json
import time
import uuid
import logging
import httpx
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import os

# Configuration
SERVICE_PORT = 5006
API_VERSION = "2.0.0"
MCP_VERSION = "1.0.0"

# Services JARVIS
SERVICES = {
    "brain-api": "http://brain-api:8080",
    "system-control": "http://system-control:5004", 
    "terminal-service": "http://terminal-service:5005",
    "tts-service": "http://tts-service:5002",
    "stt-service": "http://stt-service:5003"
}

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="JARVIS MCP Gateway",
    version=API_VERSION,
    description="Model Context Protocol Gateway pour intégrations IDE"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, restreindre aux domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MCPToolType(str, Enum):
    FUNCTION = "function"
    RESOURCE = "resource"
    PROMPT = "prompt"

class MCPResourceType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    URL = "url"
    MEMORY = "memory"
    TERMINAL = "terminal"

@dataclass
class MCPTool:
    name: str
    type: MCPToolType
    description: str
    parameters: Dict[str, Any]
    service: str
    endpoint: str
    method: str = "POST"
    
@dataclass
class MCPResource:
    uri: str
    type: MCPResourceType
    name: str
    description: str
    metadata: Dict[str, Any] = None

class MCPToolRegistry:
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.initialize_tools()
    
    def initialize_tools(self):
        """Initialise les outils MCP disponibles"""
        
        # Outils de contrôle système
        self.register_tool(MCPTool(
            name="system_mouse_click",
            type=MCPToolType.FUNCTION,
            description="Clique avec la souris à des coordonnées spécifiques",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Coordonnée X"},
                    "y": {"type": "integer", "description": "Coordonnée Y"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"}
                },
                "required": ["x", "y"]
            },
            service="system-control",
            endpoint="/mouse/click"
        ))
        
        self.register_tool(MCPTool(
            name="system_type_text",
            type=MCPToolType.FUNCTION,
            description="Tape du texte via le clavier",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Texte à taper"},
                    "interval": {"type": "number", "default": 0.05, "description": "Intervalle entre les caractères"}
                },
                "required": ["text"]
            },
            service="system-control",
            endpoint="/keyboard/type"
        ))
        
        self.register_tool(MCPTool(
            name="system_hotkey",
            type=MCPToolType.FUNCTION,
            description="Exécute une combinaison de touches",
            parameters={
                "type": "object",
                "properties": {
                    "keys": {"type": "array", "items": {"type": "string"}, "description": "Liste des touches"}
                },
                "required": ["keys"]
            },
            service="system-control",
            endpoint="/keyboard/hotkey"
        ))
        
        self.register_tool(MCPTool(
            name="system_screenshot",
            type=MCPToolType.FUNCTION,
            description="Prend une capture d'écran",
            parameters={
                "type": "object",
                "properties": {}
            },
            service="system-control",
            endpoint="/screenshot"
        ))
        
        # Outils terminal
        self.register_tool(MCPTool(
            name="terminal_execute",
            type=MCPToolType.FUNCTION,
            description="Exécute une commande dans le terminal",
            parameters={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "ID de la session terminal"},
                    "command": {"type": "string", "description": "Commande à exécuter"}
                },
                "required": ["command"]
            },
            service="terminal-service",
            endpoint="/sessions/{session_id}/execute"
        ))
        
        self.register_tool(MCPTool(
            name="terminal_create_session",
            type=MCPToolType.FUNCTION,
            description="Crée une nouvelle session terminal",
            parameters={
                "type": "object",
                "properties": {
                    "working_dir": {"type": "string", "description": "Répertoire de travail initial"}
                }
            },
            service="terminal-service",
            endpoint="/sessions"
        ))
        
        # Outils IA
        self.register_tool(MCPTool(
            name="ai_chat",
            type=MCPToolType.FUNCTION,
            description="Envoie un message au cerveau IA de JARVIS",
            parameters={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message à envoyer"},
                    "context": {"type": "object", "description": "Contexte additionnel"}
                },
                "required": ["message"]
            },
            service="brain-api",
            endpoint="/chat"
        ))
        
        # Outils vocaux
        self.register_tool(MCPTool(
            name="tts_speak",
            type=MCPToolType.FUNCTION,
            description="Convertit du texte en parole",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Texte à convertir en parole"},
                    "voice": {"type": "string", "description": "Voix à utiliser"}
                },
                "required": ["text"]
            },
            service="tts-service",
            endpoint="/speak"
        ))
        
        self.register_tool(MCPTool(
            name="stt_transcribe",
            type=MCPToolType.FUNCTION,
            description="Transcrit un fichier audio en texte",
            parameters={
                "type": "object",
                "properties": {
                    "audio_file": {"type": "string", "description": "Chemin du fichier audio"}
                },
                "required": ["audio_file"]
            },
            service="stt-service",
            endpoint="/transcribe"
        ))
        
        logger.info(f"Initialized {len(self.tools)} MCP tools")
    
    def register_tool(self, tool: MCPTool):
        """Enregistre un nouvel outil MCP"""
        self.tools[tool.name] = tool
    
    def register_resource(self, resource: MCPResource):
        """Enregistre une nouvelle ressource MCP"""
        self.resources[resource.uri] = resource
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Récupère un outil par nom"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[MCPTool]:
        """Liste tous les outils disponibles"""
        return list(self.tools.values())
    
    def list_resources(self) -> List[MCPResource]:
        """Liste toutes les ressources disponibles"""
        return list(self.resources.values())

class MCPClient:
    def __init__(self):
        self.sessions: Dict[str, Dict] = {}
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Exécute un outil MCP"""
        tool = registry.get_tool(tool_name)
        if not tool:
            raise HTTPException(404, f"Tool not found: {tool_name}")
        
        service_url = SERVICES.get(tool.service)
        if not service_url:
            raise HTTPException(500, f"Service not configured: {tool.service}")
        
        # Préparation de l'URL
        endpoint = tool.endpoint
        if "{session_id}" in endpoint and "session_id" in parameters:
            endpoint = endpoint.format(session_id=parameters.pop("session_id"))
        
        url = f"{service_url}{endpoint}"
        
        try:
            # Appel HTTP au service
            if tool.method == "GET":
                response = await self.http_client.get(url, params=parameters)
            else:
                response = await self.http_client.post(url, json=parameters)
            
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
            
        except httpx.HTTPError as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "success": False,
                "tool": tool_name,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def close(self):
        """Ferme le client HTTP"""
        await self.http_client.aclose()

# Instances globales
registry = MCPToolRegistry()
mcp_client = MCPClient()

# Modèles Pydantic
class MCPRequest(BaseModel):
    jsonrpc: str = Field("2.0", description="Version JSON-RPC")
    id: Union[str, int] = Field(..., description="ID de la requête")
    method: str = Field(..., description="Méthode à appeler")
    params: Optional[Dict[str, Any]] = Field(None, description="Paramètres")

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class ToolCallRequest(BaseModel):
    tool_name: str = Field(..., description="Nom de l'outil à exécuter")
    parameters: Dict[str, Any] = Field({}, description="Paramètres de l'outil")

# Routes MCP Standard
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "MCP Gateway",
        "version": API_VERSION,
        "mcp_version": MCP_VERSION,
        "tools_count": len(registry.tools),
        "resources_count": len(registry.resources),
        "timestamp": time.time()
    }

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest):
    """Point d'entrée principal MCP (JSON-RPC 2.0)"""
    
    try:
        if request.method == "initialize":
            return MCPResponse(
                id=request.id,
                result={
                    "protocolVersion": MCP_VERSION,
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "resources": {"subscribe": True, "listChanged": True},
                        "prompts": {"listChanged": True},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "JARVIS MCP Gateway",
                        "version": API_VERSION
                    }
                }
            )
        
        elif request.method == "tools/list":
            tools = []
            for tool in registry.list_tools():
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.parameters
                })
            
            return MCPResponse(
                id=request.id,
                result={"tools": tools}
            )
        
        elif request.method == "tools/call":
            params = request.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                return MCPResponse(
                    id=request.id,
                    error={"code": -32602, "message": "Missing tool name"}
                )
            
            result = await mcp_client.call_tool(tool_name, arguments)
            
            return MCPResponse(
                id=request.id,
                result={
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2)
                        }
                    ]
                }
            )
        
        elif request.method == "resources/list":
            resources = []
            for resource in registry.list_resources():
                resources.append({
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.metadata.get("mimeType") if resource.metadata else None
                })
            
            return MCPResponse(
                id=request.id,
                result={"resources": resources}
            )
        
        else:
            return MCPResponse(
                id=request.id,
                error={"code": -32601, "message": f"Method not found: {request.method}"}
            )
    
    except Exception as e:
        logger.error(f"MCP request error: {e}")
        return MCPResponse(
            id=request.id,
            error={"code": -32603, "message": f"Internal error: {str(e)}"}
        )

@app.get("/tools")
async def list_tools():
    """Liste tous les outils disponibles (API REST)"""
    tools = []
    for tool in registry.list_tools():
        tools.append({
            "name": tool.name,
            "type": tool.type.value,
            "description": tool.description,
            "service": tool.service,
            "parameters": tool.parameters
        })
    
    return {
        "success": True,
        "tools": tools,
        "count": len(tools)
    }

@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: ToolCallRequest):
    """Exécute un outil spécifique (API REST)"""
    result = await mcp_client.call_tool(tool_name, request.parameters)
    return result

@app.get("/resources")
async def list_resources():
    """Liste toutes les ressources disponibles"""
    resources = []
    for resource in registry.list_resources():
        resources.append(asdict(resource))
    
    return {
        "success": True,
        "resources": resources,
        "count": len(resources)
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket pour communication MCP temps réel"""
    await websocket.accept()
    session_id = str(uuid.uuid4())
    
    logger.info(f"MCP WebSocket connected: {session_id}")
    
    try:
        # Message de bienvenue
        await websocket.send_json({
            "type": "connected",
            "session_id": session_id,
            "capabilities": {
                "tools": True,
                "resources": True,
                "streaming": True
            }
        })
        
        while True:
            # Recevoir les requêtes MCP
            data = await websocket.receive_json()
            
            if data.get("type") == "mcp_request":
                # Traiter la requête MCP
                mcp_request = MCPRequest(**data.get("request", {}))
                response = await mcp_endpoint(mcp_request)
                
                await websocket.send_json({
                    "type": "mcp_response",
                    "response": response.dict()
                })
            
            elif data.get("type") == "tool_call":
                # Exécution d'outil directe
                tool_name = data.get("tool_name")
                parameters = data.get("parameters", {})
                
                if tool_name:
                    result = await mcp_client.call_tool(tool_name, parameters)
                    await websocket.send_json({
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "result": result
                    })
            
            elif data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
    
    except WebSocketDisconnect:
        logger.info(f"MCP WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"MCP WebSocket error: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Nettoyage à l'arrêt"""
    await mcp_client.close()

if __name__ == "__main__":
    logger.info(f"Starting MCP Gateway on port {SERVICE_PORT}")
    logger.info(f"Available tools: {len(registry.tools)}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=False
    )