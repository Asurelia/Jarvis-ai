"""
🌐 JARVIS Web Tools  
Outils pour les opérations web et réseau
"""
import asyncio
import aiohttp
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any
import json
import time

from .base_tool import BaseTool, ToolResult, ToolCategory, ToolParameter

class WebSearchTool(BaseTool):
    """Outil pour effectuer des recherches web"""
    
    @property
    def display_name(self) -> str:
        return "Recherche Web"
    
    @property
    def description(self) -> str:
        return "Effectue une recherche web et retourne les résultats"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                type="str",
                description="Terme de recherche",
                required=True
            ),
            ToolParameter(
                name="num_results",
                type="int",
                description="Nombre de résultats à retourner",
                required=False,
                default=5
            ),
            ToolParameter(
                name="search_engine",
                type="str",
                description="Moteur de recherche à utiliser",
                required=False,
                default="duckduckgo",
                choices=["duckduckgo", "bing"]
            ),
            ToolParameter(
                name="safe_search",
                type="bool",
                description="Activer la recherche sécurisée",
                required=False,
                default=True
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["aiohttp", "beautifulsoup4"]
    
    @property
    def permissions(self) -> List[str]:
        return ["network"]
    
    async def execute(self, query: str, num_results: int = 5, 
                     search_engine: str = "duckduckgo", safe_search: bool = True) -> ToolResult:
        try:
            if search_engine == "duckduckgo":
                results = await self._search_duckduckgo(query, num_results, safe_search)
            elif search_engine == "bing":
                results = await self._search_bing(query, num_results, safe_search)
            else:
                return ToolResult(
                    success=False,
                    error=f"Moteur de recherche non supporté: {search_engine}",
                    message="Utilisez 'duckduckgo' ou 'bing'"
                )
            
            return ToolResult(
                success=True,
                data=results,
                message=f"Recherche effectuée: {len(results)} résultats trouvés",
                metadata={
                    "query": query,
                    "search_engine": search_engine,
                    "num_results": len(results),
                    "safe_search": safe_search
                }
            )
            
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la recherche web"
            )
    
    async def _search_duckduckgo(self, query: str, num_results: int, safe_search: bool) -> List[Dict]:
        """Recherche avec DuckDuckGo"""
        try:
            from bs4 import BeautifulSoup
            
            # Paramètres de recherche
            params = {
                'q': query,
                'format': 'html',
                'no_redirect': '1'
            }
            
            if safe_search:
                params['safe_search'] = 'strict'
            
            url = "https://duckduckgo.com/"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise Exception(f"Erreur HTTP: {response.status}")
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    results = []
                    
                    # Parser les résultats
                    for result_div in soup.find_all('div', class_='result')[:num_results]:
                        title_elem = result_div.find('h2')
                        link_elem = result_div.find('a')
                        snippet_elem = result_div.find('a', class_='result__snippet')
                        
                        if title_elem and link_elem:
                            result = {
                                "title": title_elem.get_text(strip=True),
                                "url": link_elem.get('href', ''),
                                "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                            }
                            results.append(result)
                    
                    return results
                    
        except ImportError:
            raise Exception("beautifulsoup4 requis: pip install beautifulsoup4")
        except Exception as e:
            raise Exception(f"Erreur recherche DuckDuckGo: {str(e)}")
    
    async def _search_bing(self, query: str, num_results: int, safe_search: bool) -> List[Dict]:
        """Recherche avec Bing (API simplifiée)"""
        # Pour une implémentation complète, utiliser l'API Bing Search
        # Ici nous utilisons une approche basique
        return [{
            "title": f"Résultat Bing pour: {query}",
            "url": f"https://www.bing.com/search?q={urllib.parse.quote(query)}",
            "snippet": "Recherche Bing (implémentation de base)"
        }]

class WebScrapeTool(BaseTool):
    """Outil pour extraire le contenu d'une page web"""
    
    @property
    def display_name(self) -> str:
        return "Extraction Web"
    
    @property
    def description(self) -> str:
        return "Extrait le contenu textuel d'une page web"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="url",
                description="URL de la page à extraire",
                required=True
            ),
            ToolParameter(
                name="selector",
                type="str",
                description="Sélecteur CSS pour extraire un élément spécifique",
                required=False,
                default=None
            ),
            ToolParameter(
                name="format",
                type="str",
                description="Format de sortie",
                required=False,
                default="text",
                choices=["text", "html", "markdown"]
            ),
            ToolParameter(
                name="max_length",
                type="int",
                description="Longueur maximale du contenu (caractères)",
                required=False,
                default=10000
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["aiohttp", "beautifulsoup4"]
    
    @property
    def permissions(self) -> List[str]:
        return ["network"]
    
    async def execute(self, url: str, selector: str = None, 
                     format: str = "text", max_length: int = 10000) -> ToolResult:
        try:
            from bs4 import BeautifulSoup
            
            # Valider l'URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"Erreur HTTP: {response.status}",
                            message=f"Impossible d'accéder à la page: {url}"
                        )
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Sélectionner l'élément spécifique ou toute la page
                    if selector:
                        elements = soup.select(selector)
                        if not elements:
                            return ToolResult(
                                success=False,
                                error=f"Sélecteur non trouvé: {selector}",
                                message="Aucun élément correspondant au sélecteur"
                            )
                        target = elements[0]
                    else:
                        # Supprimer les scripts et styles
                        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
                            tag.decompose()
                        target = soup.find('body') or soup
                    
                    # Extraire le contenu selon le format
                    if format == "html":
                        content = str(target)
                    elif format == "markdown":
                        # Conversion basique HTML -> Markdown
                        content = self._html_to_markdown(target)
                    else:  # text
                        content = target.get_text(separator='\n', strip=True)
                    
                    # Limiter la longueur
                    if len(content) > max_length:
                        content = content[:max_length] + "..."
                    
                    return ToolResult(
                        success=True,
                        data=content,
                        message=f"Contenu extrait: {len(content)} caractères",
                        metadata={
                            "url": url,
                            "selector": selector,
                            "format": format,
                            "content_length": len(content),
                            "title": soup.title.string if soup.title else None
                        }
                    )
                    
        except ImportError:
            return ToolResult(
                success=False,
                error="beautifulsoup4 requis: pip install beautifulsoup4",
                message="Dépendance manquante"
            )
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error="Timeout",
                message="La page met trop de temps à répondre"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de l'extraction de la page"
            )
    
    def _html_to_markdown(self, soup) -> str:
        """Conversion basique HTML vers Markdown"""
        text = ""
        
        for element in soup.descendants:
            if element.name == 'h1':
                text += f"\n# {element.get_text(strip=True)}\n\n"
            elif element.name == 'h2':
                text += f"\n## {element.get_text(strip=True)}\n\n"
            elif element.name == 'h3':
                text += f"\n### {element.get_text(strip=True)}\n\n"
            elif element.name == 'p':
                text += f"{element.get_text(strip=True)}\n\n"
            elif element.name == 'a' and element.get('href'):
                text += f"[{element.get_text(strip=True)}]({element.get('href')})"
            elif element.name == 'li':
                text += f"- {element.get_text(strip=True)}\n"
        
        return text.strip()

class DownloadTool(BaseTool):
    """Outil pour télécharger des fichiers"""
    
    @property
    def display_name(self) -> str:
        return "Téléchargement de Fichier"
    
    @property
    def description(self) -> str:
        return "Télécharge un fichier depuis une URL"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.WEB
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="url",
                type="url",
                description="URL du fichier à télécharger",
                required=True
            ),
            ToolParameter(
                name="destination",
                type="str",
                description="Chemin de destination (optionnel)",
                required=False,
                default=None
            ),
            ToolParameter(
                name="max_size_mb",
                type="int",
                description="Taille maximale en MB",
                required=False,
                default=100
            ),
            ToolParameter(
                name="overwrite",
                type="bool",
                description="Écraser le fichier s'il existe",
                required=False,
                default=False
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["aiohttp"]
    
    @property
    def permissions(self) -> List[str]:
        return ["network", "file_write"]
    
    async def execute(self, url: str, destination: str = None, 
                     max_size_mb: int = 100, overwrite: bool = False) -> ToolResult:
        try:
            # Valider l'URL
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Déterminer le nom de fichier
            if destination:
                file_path = Path(destination)
            else:
                filename = Path(urllib.parse.urlparse(url).path).name
                if not filename or '.' not in filename:
                    filename = f"download_{int(time.time())}"
                file_path = Path("downloads") / filename
            
            # Créer le dossier parent
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Vérifier si le fichier existe
            if file_path.exists() and not overwrite:
                return ToolResult(
                    success=False,
                    error=f"Fichier existe déjà: {file_path}",
                    message="Utilisez overwrite=True pour écraser"
                )
            
            max_size_bytes = max_size_mb * 1024 * 1024
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"Erreur HTTP: {response.status}",
                            message=f"Impossible de télécharger: {url}"
                        )
                    
                    # Vérifier la taille
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > max_size_bytes:
                        return ToolResult(
                            success=False,
                            error=f"Fichier trop volumineux: {int(content_length) // 1024 // 1024}MB",
                            message=f"Limite: {max_size_mb}MB"
                        )
                    
                    # Télécharger le fichier
                    downloaded_size = 0
                    with open(file_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            downloaded_size += len(chunk)
                            
                            if downloaded_size > max_size_bytes:
                                f.close()
                                file_path.unlink()  # Supprimer le fichier partiel
                                return ToolResult(
                                    success=False,
                                    error=f"Fichier trop volumineux: {downloaded_size // 1024 // 1024}MB",
                                    message=f"Limite: {max_size_mb}MB"
                                )
                            
                            f.write(chunk)
                    
                    return ToolResult(
                        success=True,
                        data=str(file_path),
                        message=f"Fichier téléchargé: {downloaded_size // 1024}KB",
                        metadata={
                            "url": url,
                            "destination": str(file_path),
                            "size_bytes": downloaded_size,
                            "size_mb": round(downloaded_size / 1024 / 1024, 2),
                            "content_type": response.headers.get('content-type')
                        }
                    )
                    
        except Exception as e:
            # Nettoyer le fichier partiel en cas d'erreur
            if 'file_path' in locals() and file_path.exists():
                try:
                    file_path.unlink()
                except:
                    pass
            
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors du téléchargement"
            )