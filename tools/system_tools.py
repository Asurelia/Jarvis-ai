"""
🖥️ JARVIS System Tools
Outils système pour les opérations de fichiers et processus
"""
import os
import shutil
import psutil
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import json

from .base_tool import BaseTool, ToolResult, ToolCategory, ToolParameter

class FileReadTool(BaseTool):
    """Outil pour lire des fichiers"""
    
    @property
    def display_name(self) -> str:
        return "Lecture de Fichier"
    
    @property
    def description(self) -> str:
        return "Lit le contenu d'un fichier texte et retourne son contenu"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="filepath",
                type="str",
                description="Chemin vers le fichier à lire",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="str",
                description="Encodage du fichier",
                required=False,
                default="utf-8",
                choices=["utf-8", "ascii", "latin-1", "cp1252"]
            ),
            ToolParameter(
                name="max_lines",
                type="int",
                description="Nombre maximum de lignes à lire",
                required=False,
                default=None
            )
        ]
    
    @property
    def permissions(self) -> List[str]:
        return ["file_read"]
    
    async def execute(self, filepath: str, encoding: str = "utf-8", max_lines: int = None) -> ToolResult:
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Fichier non trouvé: {filepath}",
                    message="Le fichier spécifié n'existe pas"
                )
            
            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Le chemin ne pointe pas vers un fichier: {filepath}",
                    message="Le chemin spécifié n'est pas un fichier"
                )
            
            with open(file_path, 'r', encoding=encoding) as f:
                if max_lines:
                    content = ''.join(f.readline() for _ in range(max_lines))
                else:
                    content = f.read()
            
            file_stats = file_path.stat()
            
            return ToolResult(
                success=True,
                data=content,
                message=f"Fichier lu avec succès: {len(content)} caractères",
                metadata={
                    "filepath": str(file_path),
                    "size_bytes": file_stats.st_size,
                    "encoding": encoding,
                    "lines_read": len(content.splitlines()) if content else 0
                }
            )
            
        except UnicodeDecodeError as e:
            return ToolResult(
                success=False,
                error=f"Erreur d'encodage: {str(e)}",
                message=f"Impossible de décoder le fichier avec l'encodage {encoding}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la lecture du fichier"
            )

class FileWriteTool(BaseTool):
    """Outil pour écrire des fichiers"""
    
    @property
    def display_name(self) -> str:
        return "Écriture de Fichier"
    
    @property
    def description(self) -> str:
        return "Écrit du contenu dans un fichier texte"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="filepath",
                type="str",
                description="Chemin vers le fichier à écrire",
                required=True
            ),
            ToolParameter(
                name="content",
                type="str",
                description="Contenu à écrire dans le fichier",
                required=True
            ),
            ToolParameter(
                name="encoding",
                type="str",
                description="Encodage du fichier",
                required=False,
                default="utf-8"
            ),
            ToolParameter(
                name="append",
                type="bool",
                description="Ajouter à la fin du fichier au lieu de l'écraser",
                required=False,
                default=False
            ),
            ToolParameter(
                name="create_dirs",
                type="bool",
                description="Créer les dossiers parents si nécessaire",
                required=False,
                default=True
            )
        ]
    
    @property
    def permissions(self) -> List[str]:
        return ["file_write"]
    
    async def execute(self, filepath: str, content: str, encoding: str = "utf-8", 
                     append: bool = False, create_dirs: bool = True) -> ToolResult:
        try:
            file_path = Path(filepath)
            
            # Créer les dossiers parents si nécessaire
            if create_dirs and not file_path.parent.exists():
                file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            
            with open(file_path, mode, encoding=encoding) as f:
                f.write(content)
            
            file_stats = file_path.stat()
            
            return ToolResult(
                success=True,
                data=str(file_path),
                message=f"Fichier {'modifié' if append else 'créé'} avec succès",
                metadata={
                    "filepath": str(file_path),
                    "size_bytes": file_stats.st_size,
                    "content_length": len(content),
                    "encoding": encoding,
                    "mode": "append" if append else "write"
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de l'écriture du fichier"
            )

class DirectoryListTool(BaseTool):
    """Outil pour lister le contenu d'un dossier"""
    
    @property
    def display_name(self) -> str:
        return "Liste de Dossier"
    
    @property
    def description(self) -> str:
        return "Liste le contenu d'un dossier avec détails des fichiers"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="directory",
                type="str",
                description="Chemin vers le dossier à lister",
                required=True
            ),
            ToolParameter(
                name="recursive",
                type="bool",
                description="Lister récursivement les sous-dossiers",
                required=False,
                default=False
            ),
            ToolParameter(
                name="show_hidden",
                type="bool",
                description="Afficher les fichiers cachés",
                required=False,
                default=False
            ),
            ToolParameter(
                name="filter_extension",
                type="str",
                description="Filtrer par extension (ex: .txt, .py)",
                required=False,
                default=None
            )
        ]
    
    @property
    def permissions(self) -> List[str]:
        return ["file_read"]
    
    async def execute(self, directory: str, recursive: bool = False, 
                     show_hidden: bool = False, filter_extension: str = None) -> ToolResult:
        try:
            dir_path = Path(directory)
            
            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Dossier non trouvé: {directory}",
                    message="Le dossier spécifié n'existe pas"
                )
            
            if not dir_path.is_dir():
                return ToolResult(
                    success=False,
                    error=f"Le chemin ne pointe pas vers un dossier: {directory}",
                    message="Le chemin spécifié n'est pas un dossier"
                )
            
            files_info = []
            total_size = 0
            
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"
            
            for item in dir_path.glob(pattern):
                # Filtrer les fichiers cachés
                if not show_hidden and item.name.startswith('.'):
                    continue
                
                # Filtrer par extension
                if filter_extension and item.is_file():
                    if not item.name.lower().endswith(filter_extension.lower()):
                        continue
                
                try:
                    stat = item.stat()
                    item_info = {
                        "name": item.name,
                        "path": str(item),
                        "type": "directory" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else 0,
                        "modified": stat.st_mtime,
                        "permissions": oct(stat.st_mode)[-3:]
                    }
                    
                    if item.is_file():
                        item_info["extension"] = item.suffix
                        total_size += stat.st_size
                    
                    files_info.append(item_info)
                    
                except (OSError, PermissionError):
                    # Ignorer les fichiers inaccessibles
                    continue
            
            # Trier par nom
            files_info.sort(key=lambda x: (x["type"] == "file", x["name"].lower()))
            
            return ToolResult(
                success=True,
                data=files_info,
                message=f"Dossier listé: {len(files_info)} éléments trouvés",
                metadata={
                    "directory": str(dir_path),
                    "total_items": len(files_info),
                    "total_size": total_size,
                    "recursive": recursive,
                    "filter_extension": filter_extension
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la lecture du dossier"
            )

class ProcessListTool(BaseTool):
    """Outil pour lister les processus système"""
    
    @property
    def display_name(self) -> str:
        return "Liste des Processus"
    
    @property
    def description(self) -> str:
        return "Liste les processus système en cours d'exécution"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SYSTEM
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="filter_name",
                type="str",
                description="Filtrer par nom de processus",
                required=False,
                default=None
            ),
            ToolParameter(
                name="sort_by",
                type="str",
                description="Trier par critère",
                required=False,
                default="memory_percent",
                choices=["pid", "name", "cpu_percent", "memory_percent", "create_time"]
            ),
            ToolParameter(
                name="limit",
                type="int",
                description="Nombre maximum de processus à retourner",
                required=False,
                default=50
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["psutil"]
    
    @property
    def permissions(self) -> List[str]:
        return ["system"]
    
    async def execute(self, filter_name: str = None, sort_by: str = "memory_percent", 
                     limit: int = 50) -> ToolResult:
        try:
            processes_info = []
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                           'memory_percent', 'memory_info', 'create_time', 'status']):
                try:
                    proc_info = proc.info
                    
                    # Filtrer par nom si spécifié
                    if filter_name and filter_name.lower() not in proc_info['name'].lower():
                        continue
                    
                    # Formater les informations
                    process_data = {
                        "pid": proc_info['pid'],
                        "name": proc_info['name'],
                        "username": proc_info['username'] or "N/A",
                        "cpu_percent": proc_info['cpu_percent'] or 0.0,
                        "memory_percent": proc_info['memory_percent'] or 0.0,
                        "memory_mb": round(proc_info['memory_info'].rss / 1024 / 1024, 1) if proc_info['memory_info'] else 0,
                        "status": proc_info['status'],
                        "create_time": proc_info['create_time']
                    }
                    
                    processes_info.append(process_data)
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Trier les processus
            if sort_by in ['cpu_percent', 'memory_percent', 'memory_mb']:
                processes_info.sort(key=lambda x: x[sort_by], reverse=True)
            else:
                processes_info.sort(key=lambda x: x[sort_by])
            
            # Limiter le nombre de résultats
            processes_info = processes_info[:limit]
            
            return ToolResult(
                success=True,
                data=processes_info,
                message=f"Liste des processus: {len(processes_info)} processus trouvés",
                metadata={
                    "total_processes": len(processes_info),
                    "filter_name": filter_name,
                    "sort_by": sort_by,
                    "limit": limit
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la récupération des processus"
            )

class SystemInfoTool(BaseTool):
    """Outil pour obtenir les informations système"""
    
    @property
    def display_name(self) -> str:
        return "Informations Système"
    
    @property
    def description(self) -> str:
        return "Récupère les informations détaillées du système (CPU, RAM, disque, etc.)"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.SYSTEM
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="include_network",
                type="bool",
                description="Inclure les informations réseau",
                required=False,
                default=True
            ),
            ToolParameter(
                name="include_disks",
                type="bool",
                description="Inclure les informations des disques",
                required=False,
                default=True
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["psutil"]
    
    @property
    def permissions(self) -> List[str]:
        return ["system"]
    
    async def execute(self, include_network: bool = True, include_disks: bool = True) -> ToolResult:
        try:
            system_info = {}
            
            # Informations de base
            system_info["platform"] = {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version()
            }
            
            # CPU
            system_info["cpu"] = {
                "logical_cores": psutil.cpu_count(logical=True),
                "physical_cores": psutil.cpu_count(logical=False),
                "current_freq": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "usage_percent": psutil.cpu_percent(interval=1),
                "load_avg": os.getloadavg() if hasattr(os, 'getloadavg') else None
            }
            
            # Mémoire
            memory = psutil.virtual_memory()
            system_info["memory"] = {
                "total_gb": round(memory.total / 1024**3, 2),
                "available_gb": round(memory.available / 1024**3, 2),
                "used_gb": round(memory.used / 1024**3, 2),
                "usage_percent": memory.percent,
                "free_gb": round(memory.free / 1024**3, 2)
            }
            
            # Swap
            swap = psutil.swap_memory()
            system_info["swap"] = {
                "total_gb": round(swap.total / 1024**3, 2),
                "used_gb": round(swap.used / 1024**3, 2),
                "free_gb": round(swap.free / 1024**3, 2),
                "usage_percent": swap.percent
            }
            
            # Disques
            if include_disks:
                disks = []
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_info = {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "filesystem": partition.fstype,
                            "total_gb": round(usage.total / 1024**3, 2),
                            "used_gb": round(usage.used / 1024**3, 2),
                            "free_gb": round(usage.free / 1024**3, 2),
                            "usage_percent": round((usage.used / usage.total) * 100, 1)
                        }
                        disks.append(disk_info)
                    except PermissionError:
                        continue
                
                system_info["disks"] = disks
            
            # Réseau
            if include_network:
                network_stats = psutil.net_io_counters()
                system_info["network"] = {
                    "bytes_sent": network_stats.bytes_sent,
                    "bytes_recv": network_stats.bytes_recv,
                    "packets_sent": network_stats.packets_sent,
                    "packets_recv": network_stats.packets_recv,
                    "errors_in": network_stats.errin,
                    "errors_out": network_stats.errout
                }
                
                # Interfaces réseau
                interfaces = []
                for interface, addresses in psutil.net_if_addrs().items():
                    interface_info = {"name": interface, "addresses": []}
                    for addr in addresses:
                        interface_info["addresses"].append({
                            "family": str(addr.family),
                            "address": addr.address,
                            "netmask": addr.netmask,
                            "broadcast": addr.broadcast
                        })
                    interfaces.append(interface_info)
                
                system_info["network"]["interfaces"] = interfaces
            
            # Temps de fonctionnement
            boot_time = psutil.boot_time()
            system_info["uptime"] = {
                "boot_time": boot_time,
                "uptime_seconds": time.time() - boot_time
            }
            
            return ToolResult(
                success=True,
                data=system_info,
                message="Informations système récupérées avec succès",
                metadata={
                    "timestamp": time.time(),
                    "include_network": include_network,
                    "include_disks": include_disks
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la récupération des informations système"
            )