"""
🤖 JARVIS AI Tools
Outils basés sur l'intelligence artificielle
"""
import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

from .base_tool import BaseTool, ToolResult, ToolCategory, ToolParameter

class TextGenerationTool(BaseTool):
    """Outil pour générer du texte avec l'IA"""
    
    @property
    def display_name(self) -> str:
        return "Génération de Texte"
    
    @property
    def description(self) -> str:
        return "Génère du texte créatif ou informatif à partir d'un prompt"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.AI
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="prompt",
                type="str",
                description="Prompt pour la génération de texte",
                required=True
            ),
            ToolParameter(
                name="max_tokens",
                type="int",
                description="Nombre maximum de tokens à générer",
                required=False,
                default=500
            ),
            ToolParameter(
                name="temperature",
                type="float",
                description="Créativité du modèle (0.0 à 1.0)",
                required=False,
                default=0.7
            ),
            ToolParameter(
                name="model",
                type="str",
                description="Modèle à utiliser",
                required=False,
                default="llama3.2:3b",
                choices=["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b", "mistral:7b"]
            ),
            ToolParameter(
                name="system_prompt",
                type="str",
                description="Instructions système pour le modèle",
                required=False,
                default="Tu es un assistant IA utile et créatif."
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["aiohttp"]
    
    @property
    def permissions(self) -> List[str]:
        return ["network"]
    
    async def execute(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7,
                     model: str = "llama3.2:3b", system_prompt: str = "Tu es un assistant IA utile et créatif.") -> ToolResult:
        try:
            # URL de l'API Ollama
            url = "http://localhost:11434/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"Erreur API Ollama: {response.status}",
                            message="Impossible de générer le texte"
                        )
                    
                    result = await response.json()
                    generated_text = result.get("response", "")
                    
                    return ToolResult(
                        success=True,
                        data=generated_text,
                        message=f"Texte généré: {len(generated_text)} caractères",
                        metadata={
                            "model": model,
                            "prompt_length": len(prompt),
                            "generated_length": len(generated_text),
                            "temperature": temperature,
                            "max_tokens": max_tokens
                        }
                    )
                    
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error="Timeout",
                message="La génération a pris trop de temps"
            )
        except aiohttp.ClientConnectorError:
            return ToolResult(
                success=False,
                error="Connexion impossible",
                message="Ollama n'est pas accessible sur localhost:11434"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la génération de texte"
            )

class ImageAnalysisTool(BaseTool):
    """Outil pour analyser des images avec l'IA"""
    
    @property
    def display_name(self) -> str:
        return "Analyse d'Image"
    
    @property
    def description(self) -> str:
        return "Analyse le contenu d'une image et fournit une description détaillée"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.AI
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="image_path",
                type="file",
                description="Chemin vers l'image à analyser",
                required=True
            ),
            ToolParameter(
                name="analysis_type",
                type="str",
                description="Type d'analyse à effectuer",
                required=False,
                default="general",
                choices=["general", "detailed", "objects", "text", "scene"]
            ),
            ToolParameter(
                name="model",
                type="str",
                description="Modèle de vision à utiliser",
                required=False,
                default="llava:7b",
                choices=["llava:7b", "llava:13b", "bakllava:7b"]
            ),
            ToolParameter(
                name="prompt",
                type="str",
                description="Prompt personnalisé pour l'analyse",
                required=False,
                default="Décris cette image en détail."
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["aiohttp", "base64"]
    
    @property
    def permissions(self) -> List[str]:
        return ["file_read", "network"]
    
    async def execute(self, image_path: str, analysis_type: str = "general",
                     model: str = "llava:7b", prompt: str = "Décris cette image en détail.") -> ToolResult:
        try:
            import base64
            
            # Vérifier que le fichier existe
            file_path = Path(image_path)
            if not file_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Fichier image non trouvé: {image_path}",
                    message="Le fichier image spécifié n'existe pas"
                )
            
            # Lire et encoder l'image en base64
            try:
                with open(file_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Impossible de lire l'image: {str(e)}",
                    message="Erreur lors de la lecture du fichier image"
                )
            
            # Adapter le prompt selon le type d'analyse
            analysis_prompts = {
                "general": "Décris cette image en détail.",
                "detailed": "Analyse cette image de manière très détaillée, incluant les objets, les couleurs, la composition, l'ambiance.",
                "objects": "Liste tous les objets visibles dans cette image.",
                "text": "Extrais et transcris tout le texte visible dans cette image.",
                "scene": "Décris la scène: où cela se passe-t-il? Quelle est l'ambiance? Que se passe-t-il?"
            }
            
            final_prompt = analysis_prompts.get(analysis_type, prompt)
            
            # URL de l'API Ollama pour la vision
            url = "http://localhost:11434/api/generate"
            
            payload = {
                "model": model,
                "prompt": final_prompt,
                "images": [image_data],
                "stream": False
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"Erreur API Ollama Vision: {response.status}",
                            message="Impossible d'analyser l'image"
                        )
                    
                    result = await response.json()
                    analysis = result.get("response", "")
                    
                    return ToolResult(
                        success=True,
                        data=analysis,
                        message=f"Image analysée: {len(analysis)} caractères de description",
                        metadata={
                            "image_path": str(file_path),
                            "image_size": file_path.stat().st_size,
                            "model": model,
                            "analysis_type": analysis_type,
                            "description_length": len(analysis)
                        }
                    )
                    
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error="Timeout",
                message="L'analyse d'image a pris trop de temps"
            )
        except aiohttp.ClientConnectorError:
            return ToolResult(
                success=False,
                error="Connexion impossible",
                message="Ollama n'est pas accessible sur localhost:11434"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de l'analyse d'image"
            )

class TranslationTool(BaseTool):
    """Outil pour traduire du texte"""
    
    @property
    def display_name(self) -> str:
        return "Traduction de Texte"
    
    @property
    def description(self) -> str:
        return "Traduit du texte d'une langue à une autre"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.AI
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="text",
                type="str",
                description="Texte à traduire",
                required=True
            ),
            ToolParameter(
                name="source_language",
                type="str",
                description="Langue source",
                required=False,
                default="auto",
                choices=["auto", "fr", "en", "es", "de", "it", "pt", "ru", "zh", "ja", "ar"]
            ),
            ToolParameter(
                name="target_language",
                type="str",
                description="Langue cible",
                required=True,
                choices=["fr", "en", "es", "de", "it", "pt", "ru", "zh", "ja", "ar"]
            ),
            ToolParameter(
                name="model",
                type="str",
                description="Modèle de traduction à utiliser",
                required=False,
                default="llama3.2:3b",
                choices=["llama3.2:3b", "llama3.1:8b", "qwen2.5:7b"]
            ),
            ToolParameter(
                name="preserve_format",
                type="bool",
                description="Préserver le formatage du texte original",
                required=False,
                default=True
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["aiohttp"]
    
    @property
    def permissions(self) -> List[str]:
        return ["network"]
    
    async def execute(self, text: str, target_language: str, source_language: str = "auto",
                     model: str = "llama3.2:3b", preserve_format: bool = True) -> ToolResult:
        try:
            # Dictionnaire des langues
            languages = {
                "fr": "français",
                "en": "anglais",
                "es": "espagnol",
                "de": "allemand",
                "it": "italien",
                "pt": "portugais",
                "ru": "russe",
                "zh": "chinois",
                "ja": "japonais",
                "ar": "arabe"
            }
            
            target_lang_name = languages.get(target_language, target_language)
            
            # Construire le prompt de traduction
            if source_language == "auto":
                prompt = f"Traduis le texte suivant en {target_lang_name}. "
            else:
                source_lang_name = languages.get(source_language, source_language)
                prompt = f"Traduis le texte suivant du {source_lang_name} vers le {target_lang_name}. "
            
            if preserve_format:
                prompt += "Préserve le formatage, la ponctuation et la structure du texte original. "
            
            prompt += f"Réponds uniquement avec la traduction, sans explication:\n\n{text}"
            
            # URL de l'API Ollama
            url = "http://localhost:11434/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3  # Moins de créativité pour les traductions
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"Erreur API Ollama: {response.status}",
                            message="Impossible de traduire le texte"
                        )
                    
                    result = await response.json()
                    translation = result.get("response", "").strip()
                    
                    # Nettoyer la réponse si elle contient des explications
                    if translation.startswith("Voici la traduction"):
                        lines = translation.split('\n')
                        translation = '\n'.join(lines[1:]).strip()
                    
                    return ToolResult(
                        success=True,
                        data=translation,
                        message=f"Texte traduit vers {target_lang_name}",
                        metadata={
                            "source_language": source_language,
                            "target_language": target_language,
                            "original_length": len(text),
                            "translation_length": len(translation),
                            "model": model,
                            "preserve_format": preserve_format
                        }
                    )
                    
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error="Timeout",
                message="La traduction a pris trop de temps"
            )
        except aiohttp.ClientConnectorError:
            return ToolResult(
                success=False,
                error="Connexion impossible",
                message="Ollama n'est pas accessible sur localhost:11434"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la traduction"
            )

class CodeAnalysisTool(BaseTool):
    """Outil pour analyser du code source"""
    
    @property
    def display_name(self) -> str:
        return "Analyse de Code"
    
    @property
    def description(self) -> str:
        return "Analyse du code source pour détecter des erreurs, optimisations et améliorations"
    
    @property
    def category(self) -> ToolCategory:
        return ToolCategory.AI
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="str",
                description="Code source à analyser",
                required=True
            ),
            ToolParameter(
                name="language",
                type="str",
                description="Langage de programmation",
                required=False,
                default="python",
                choices=["python", "javascript", "java", "c++", "c#", "go", "rust", "php", "ruby"]
            ),
            ToolParameter(
                name="analysis_type",
                type="str",
                description="Type d'analyse à effectuer",
                required=False,
                default="complete",
                choices=["complete", "errors", "optimization", "security", "style", "documentation"]
            ),
            ToolParameter(
                name="model",
                type="str",
                description="Modèle de code à utiliser",
                required=False,
                default="qwen2.5-coder:7b",
                choices=["qwen2.5-coder:7b", "llama3.1:8b", "codellama:7b"]
            )
        ]
    
    @property
    def dependencies(self) -> List[str]:
        return ["aiohttp"]
    
    @property
    def permissions(self) -> List[str]:
        return ["network"]
    
    async def execute(self, code: str, language: str = "python", analysis_type: str = "complete",
                     model: str = "qwen2.5-coder:7b") -> ToolResult:
        try:
            # Prompts spécialisés selon le type d'analyse
            analysis_prompts = {
                "complete": f"Analyse ce code {language} de manière complète. Identifie les erreurs potentielles, les optimisations possibles, les problèmes de sécurité et les améliorations de style:",
                "errors": f"Analyse ce code {language} et identifie uniquement les erreurs potentielles et bugs:",
                "optimization": f"Analyse ce code {language} et suggère des optimisations de performance:",
                "security": f"Analyse ce code {language} et identifie les vulnérabilités de sécurité potentielles:",
                "style": f"Analyse ce code {language} et suggère des améliorations de style et lisibilité:",
                "documentation": f"Analyse ce code {language} et suggère comment améliorer la documentation:"
            }
            
            prompt = analysis_prompts.get(analysis_type, analysis_prompts["complete"])
            prompt += f"\n\n```{language}\n{code}\n```\n\nFournis une analyse structurée avec des recommandations concrètes."
            
            # URL de l'API Ollama
            url = "http://localhost:11434/api/generate"
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2  # Peu de créativité pour l'analyse de code
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=90) as response:
                    if response.status != 200:
                        return ToolResult(
                            success=False,
                            error=f"Erreur API Ollama: {response.status}",
                            message="Impossible d'analyser le code"
                        )
                    
                    result = await response.json()
                    analysis = result.get("response", "")
                    
                    return ToolResult(
                        success=True,
                        data=analysis,
                        message=f"Code {language} analysé ({analysis_type})",
                        metadata={
                            "language": language,
                            "analysis_type": analysis_type,
                            "code_length": len(code),
                            "analysis_length": len(analysis),
                            "model": model
                        }
                    )
                    
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error="Timeout",
                message="L'analyse de code a pris trop de temps"
            )
        except aiohttp.ClientConnectorError:
            return ToolResult(
                success=False,
                error="Connexion impossible",
                message="Ollama n'est pas accessible sur localhost:11434"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de l'analyse de code"
            )