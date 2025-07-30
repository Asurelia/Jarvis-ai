#!/usr/bin/env python3
"""
🧪 Test du système de personas JARVIS
Script de test pour vérifier le fonctionnement des personas
"""

import asyncio
import json
import aiohttp
import time
from typing import Dict, Any

class PersonaTestSuite:
    """Suite de tests pour le système de personas"""
    
    def __init__(self, api_url: str = "http://localhost:8001/api/persona"):
        self.api_url = api_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_get_personas(self) -> Dict[str, Any]:
        """Test récupération des personas disponibles"""
        print("🔍 Test: Récupération des personas...")
        
        try:
            async with self.session.get(f"{self.api_url}/") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ {len(data)} personas trouvées")
                    for name, info in data.items():
                        print(f"   - {info['name']}: {info['description'][:50]}...")
                    return {"success": True, "data": data}
                else:
                    print(f"❌ Erreur {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_get_current_persona(self) -> Dict[str, Any]:
        """Test récupération de la persona actuelle"""
        print("🎭 Test: Persona actuelle...")
        
        try:
            async with self.session.get(f"{self.api_url}/current") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Persona actuelle: {data['name']}")
                    return {"success": True, "current": data['name']}
                else:
                    print(f"❌ Erreur {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_switch_persona(self, persona_name: str) -> Dict[str, Any]:
        """Test changement de persona"""
        print(f"🔄 Test: Changement vers {persona_name}...")
        
        try:
            payload = {
                "reason": "test_suite",
                "user_id": "test_user",
                "context": {
                    "test_mode": True,
                    "timestamp": time.time()
                }
            }
            
            async with self.session.post(
                f"{self.api_url}/switch/{persona_name}",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["success"]:
                        print(f"✅ Changement réussi: {data['previous_persona']} → {data['current_persona']}")
                        return {"success": True, "data": data}
                    else:
                        print(f"❌ Changement échoué")
                        return {"success": False, "error": "Switch failed"}
                else:
                    print(f"❌ Erreur {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_format_response(self, content: str, context: Dict = None) -> Dict[str, Any]:
        """Test formatage de réponse avec persona"""
        print(f"✨ Test: Formatage de '{content[:30]}...'")
        
        try:
            payload = {
                "content": content,
                "context": context or {}
            }
            
            async with self.session.post(
                f"{self.api_url}/format",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Formaté par {data['persona']}:")
                    print(f"   Original: {data['original']}")
                    print(f"   Formaté:  {data['formatted']}")
                    return {"success": True, "data": data}
                else:
                    print(f"❌ Erreur {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_statistics(self) -> Dict[str, Any]:
        """Test récupération des statistiques"""
        print("📊 Test: Statistiques...")
        
        try:
            async with self.session.get(f"{self.api_url}/statistics") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Stats: {data['total_interactions']} interactions, "
                          f"{data['total_transitions']} transitions")
                    print(f"   Persona actuelle: {data['current_persona']}")
                    return {"success": True, "data": data}
                else:
                    print(f"❌ Erreur {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_persona_info(self, persona_name: str) -> Dict[str, Any]:
        """Test récupération d'infos sur une persona spécifique"""
        print(f"ℹ️ Test: Infos {persona_name}...")
        
        try:
            async with self.session.get(f"{self.api_url}/{persona_name}/info") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Infos {data['name']}:")
                    print(f"   Style: {data['response_style']}")
                    print(f"   Priorités: {', '.join(data['priorities'])}")
                    print(f"   Utilisations: {data['usage_count']}")
                    return {"success": True, "data": data}
                else:
                    print(f"❌ Erreur {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            print(f"❌ Exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def run_full_test_suite(self):
        """Exécuter tous les tests"""
        print("🚀 Démarrage de la suite de tests personas JARVIS\n")
        
        results = {}
        
        # Test 1: Récupérer les personas
        results["get_personas"] = await self.test_get_personas()
        print()
        
        # Test 2: Persona actuelle  
        current_result = await self.test_get_current_persona()
        results["current_persona"] = current_result
        print()
        
        # Test 3: Changements de persona
        personas_to_test = ["friday", "edith", "jarvis_classic"]
        for persona in personas_to_test:
            results[f"switch_{persona}"] = await self.test_switch_persona(persona)
            print()
            
            # Test formatage avec chaque persona
            test_content = "Hello, I need help with a complex security analysis."
            results[f"format_{persona}"] = await self.test_format_response(
                test_content, 
                {"task_type": "security", "urgency": "high"}
            )
            print()
        
        # Test 4: Statistiques
        results["statistics"] = await self.test_statistics()
        print()
        
        # Test 5: Infos détaillées de chaque persona
        for persona in personas_to_test:
            results[f"info_{persona}"] = await self.test_persona_info(persona)
            print()
        
        # Résumé des résultats
        self._print_test_summary(results)
        
        return results
    
    def _print_test_summary(self, results: Dict[str, Dict]):
        """Afficher le résumé des tests"""
        print("=" * 60)
        print("📋 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get("success", False))
        failed_tests = total_tests - passed_tests
        
        print(f"Total des tests: {total_tests}")
        print(f"✅ Réussis: {passed_tests}")
        print(f"❌ Échoués: {failed_tests}")
        print(f"📊 Taux de réussite: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Tests échoués:")
            for name, result in results.items():
                if not result.get("success", False):
                    print(f"   - {name}: {result.get('error', 'Erreur inconnue')}")
        
        print("=" * 60)


async def main():
    """Point d'entrée principal"""
    print("🎭 Test du système de personas JARVIS AI")
    print("=" * 60)
    
    try:
        async with PersonaTestSuite() as test_suite:
            results = await test_suite.run_full_test_suite()
            
            # Sauvegarder les résultats
            with open("test_results_personas.json", "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 Résultats sauvegardés dans test_results_personas.json")
            
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n💥 Erreur critique: {e}")


if __name__ == "__main__":
    asyncio.run(main())