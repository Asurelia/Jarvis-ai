#!/usr/bin/env python3
"""
🛠️ JARVIS Tools - Démonstration
Script de démonstration du système d'outils
"""
import asyncio
import sys
from pathlib import Path

# Ajouter le dossier parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from tools.tool_manager import tool_manager
from tools.mcp_server import mcp_server
from loguru import logger

async def demo_basic_tools():
    """Démonstration des outils de base"""
    logger.info("🎯 === Démonstration des Outils de Base ===")
    
    # Test de l'outil de lecture de fichier
    logger.info("📖 Test de lecture de fichier...")
    result = await tool_manager.execute_tool("FileReadTool", {
        "filepath": __file__,
        "max_lines": 10
    })
    
    if result.success:
        logger.success(f"✅ Fichier lu: {len(result.data)} caractères")
        print(f"Aperçu: {result.data[:200]}...")
    else:
        logger.error(f"❌ Erreur: {result.error}")
    
    # Test de l'outil d'informations système
    logger.info("💻 Test d'informations système...")
    result = await tool_manager.execute_tool("SystemInfoTool", {
        "include_network": False,
        "include_disks": False
    })
    
    if result.success:
        logger.success("✅ Informations système récupérées")
        print(f"Système: {result.data['platform']['system']}")
        print(f"RAM: {result.data['memory']['total_gb']} GB")
        print(f"CPU: {result.data['cpu']['logical_cores']} cœurs")
    else:
        logger.error(f"❌ Erreur: {result.error}")

async def demo_search_tools():
    """Démonstration de la recherche d'outils"""
    logger.info("🔍 === Démonstration de la Recherche d'Outils ===")
    
    # Rechercher des outils pour lire des fichiers
    logger.info("Recherche: 'lire fichier'")
    matches = tool_manager.search_tools("lire fichier", max_results=3)
    
    for i, match in enumerate(matches, 1):
        tool_info = match["tool"]
        similarity = match["similarity"]
        logger.info(f"{i}. {tool_info['display_name']} (similarité: {similarity:.2f})")
        logger.info(f"   → {tool_info['description']}")
    
    # Rechercher des outils d'IA
    logger.info("Recherche: 'intelligence artificielle'")
    matches = tool_manager.search_tools("intelligence artificielle", max_results=3)
    
    for i, match in enumerate(matches, 1):
        tool_info = match["tool"]
        similarity = match["similarity"]
        logger.info(f"{i}. {tool_info['display_name']} (similarité: {similarity:.2f})")
        logger.info(f"   → {tool_info['description']}")

async def demo_ai_tools():
    """Démonstration des outils IA (si Ollama est disponible)"""
    logger.info("🤖 === Démonstration des Outils IA ===")
    
    # Test de génération de texte
    logger.info("✍️ Test de génération de texte...")
    result = await tool_manager.execute_tool("TextGenerationTool", {
        "prompt": "Écris un court poème sur l'intelligence artificielle",
        "max_tokens": 200,
        "temperature": 0.8
    })
    
    if result.success:
        logger.success("✅ Texte généré:")
        print(f"\n{result.data}\n")
    else:
        logger.warning(f"⚠️ Génération échouée: {result.error}")
    
    # Test de traduction
    logger.info("🌐 Test de traduction...")
    result = await tool_manager.execute_tool("TranslationTool", {
        "text": "Hello, how are you today?",
        "source_language": "en",
        "target_language": "fr"
    })
    
    if result.success:
        logger.success("✅ Texte traduit:")
        print(f"Original: Hello, how are you today?")
        print(f"Traduit: {result.data}")
    else:
        logger.warning(f"⚠️ Traduction échouée: {result.error}")

async def demo_web_tools():
    """Démonstration des outils web"""
    logger.info("🌐 === Démonstration des Outils Web ===")
    
    # Test de recherche web
    logger.info("🔍 Test de recherche web...")
    result = await tool_manager.execute_tool("WebSearchTool", {
        "query": "intelligence artificielle 2024",
        "num_results": 3,
        "search_engine": "duckduckgo"
    })
    
    if result.success:
        logger.success(f"✅ Recherche effectuée: {len(result.data)} résultats")
        for i, res in enumerate(result.data[:2], 1):
            print(f"{i}. {res['title']}")
            print(f"   URL: {res['url']}")
            print(f"   Aperçu: {res['snippet'][:100]}...")
    else:
        logger.error(f"❌ Recherche échouée: {result.error}")

async def demo_by_query():
    """Démonstration d'exécution par requête naturelle"""
    logger.info("💭 === Démonstration d'Exécution par Requête ===")
    
    # Exécuter un outil via une requête en langage naturel
    queries = [
        "lire le contenu d'un fichier",
        "obtenir les informations du système",
        "chercher sur le web"
    ]
    
    for query in queries:
        logger.info(f"Requête: '{query}'")
        result = await tool_manager.execute_tool_by_query(query)
        
        if result.success:
            logger.success(f"✅ Outil exécuté: {result.message}")
        else:
            logger.error(f"❌ Échec: {result.error}")

async def demo_mcp_server():
    """Démonstration du serveur MCP"""
    logger.info("🔌 === Démonstration du Serveur MCP ===")
    
    # Simuler une requête MCP
    from tools.mcp_server import MCPRequest, MCPResponse
    
    # Test de liste des outils
    request = MCPRequest(
        id="test-1",
        method="tools/list",
        params={}
    )
    
    response = await mcp_server.handle_list_tools(request)
    
    if response.result:
        tools_count = len(response.result["tools"])
        logger.success(f"✅ MCP: {tools_count} outils disponibles")
        
        # Afficher quelques outils
        for tool in response.result["tools"][:3]:
            print(f"- {tool['name']}: {tool['description']}")
    else:
        logger.error(f"❌ MCP Error: {response.error}")

async def main():
    """Fonction principale de démonstration"""
    logger.info("🛠️ === JARVIS Tools - Démonstration Complète ===")
    
    # Initialiser le gestionnaire d'outils
    logger.info("🚀 Initialisation du gestionnaire d'outils...")
    success = await tool_manager.initialize()
    
    if not success:
        logger.error("❌ Impossible d'initialiser le gestionnaire d'outils")
        return
    
    # Afficher les statistiques
    stats = tool_manager.get_stats()
    logger.info(f"📊 Statistiques: {stats['tools_available']} outils disponibles")
    
    # Lister les outils par catégorie
    logger.info("📋 Outils disponibles par catégorie:")
    for category, count in stats['categories'].items():
        if count > 0:
            logger.info(f"  {category}: {count} outils")
    
    print("\n" + "="*60 + "\n")
    
    # Exécuter les démos
    try:
        await demo_basic_tools()
        print("\n" + "="*60 + "\n")
        
        await demo_search_tools()
        print("\n" + "="*60 + "\n")
        
        await demo_web_tools()
        print("\n" + "="*60 + "\n")
        
        await demo_by_query()
        print("\n" + "="*60 + "\n")
        
        await demo_mcp_server()
        print("\n" + "="*60 + "\n")
        
        # Les outils IA nécessitent Ollama
        logger.info("💡 Pour tester les outils IA, assurez-vous qu'Ollama est démarré")
        await demo_ai_tools()
        
    except KeyboardInterrupt:
        logger.info("👋 Démonstration interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur durant la démonstration: {e}")
    
    # Statistiques finales
    final_stats = tool_manager.get_stats()
    logger.info("📊 Statistiques finales:")
    logger.info(f"  Outils exécutés: {final_stats['tools_executed']}")
    logger.info(f"  Succès: {final_stats['executions_successful']}")
    logger.info(f"  Échecs: {final_stats['executions_failed']}")
    if final_stats['tools_executed'] > 0:
        logger.info(f"  Taux de succès: {final_stats['success_rate']:.1%}")
        logger.info(f"  Temps moyen: {final_stats['avg_execution_time']:.2f}s")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Au revoir!")
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")