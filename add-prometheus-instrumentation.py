#!/usr/bin/env python3
"""
🔍 JARVIS AI 2025 - Script d'ajout automatique d'instrumentation Prometheus
Script Python pour ajouter rapidement les métriques aux services manquants
"""

import os
import sys
from pathlib import Path

def add_prometheus_to_requirements(service_path):
    """Ajoute prometheus-client aux requirements.txt"""
    req_file = service_path / "requirements.txt"
    
    if not req_file.exists():
        print(f"❌ {req_file} n'existe pas")
        return False
    
    # Lire le contenu existant
    content = req_file.read_text()
    
    # Vérifier si prometheus-client est déjà présent
    if "prometheus-client" in content:
        print(f"✅ prometheus-client déjà présent dans {req_file}")
        return True
    
    # Ajouter les dépendances
    monitoring_deps = """
# Monitoring
prometheus-client==0.19.0
structlog==23.2.0
psutil==5.9.6
"""
    
    # Ajouter à la fin
    new_content = content.rstrip() + monitoring_deps
    req_file.write_text(new_content)
    
    print(f"✅ Ajouté prometheus-client à {req_file}")
    return True

def add_prometheus_imports(main_file):
    """Ajoute les imports Prometheus au main.py"""
    if not main_file.exists():
        print(f"❌ {main_file} n'existe pas")
        return False
    
    content = main_file.read_text()
    
    # Vérifier si déjà présent
    if "prometheus_client" in content:
        print(f"✅ Imports Prometheus déjà présents dans {main_file}")
        return True
    
    # Trouver la ligne d'import FastAPI
    lines = content.split('\n')
    fastapi_import_line = -1
    
    for i, line in enumerate(lines):
        if "from fastapi import" in line:
            fastapi_import_line = i
            break
    
    if fastapi_import_line == -1:
        print(f"❌ Import FastAPI non trouvé dans {main_file}")
        return False
    
    # Ajouter Response à l'import FastAPI
    if "Response" not in lines[fastapi_import_line]:
        lines[fastapi_import_line] = lines[fastapi_import_line].replace(
            "from fastapi import", 
            "from fastapi import Response,"
        ).replace(",Response,", ", Response,")
    
    # Ajouter les imports Prometheus après les imports FastAPI
    prometheus_imports = [
        "",
        "# Prometheus monitoring",
        "from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST",
        "import structlog",
        "import psutil"
    ]
    
    # Insérer après l'import FastAPI
    for i, imp in enumerate(reversed(prometheus_imports)):
        lines.insert(fastapi_import_line + 1, imp)
    
    main_file.write_text('\n'.join(lines))
    print(f"✅ Ajouté imports Prometheus à {main_file}")
    return True

def add_metrics_definitions(main_file, service_name):
    """Ajoute les définitions de métriques"""
    content = main_file.read_text()
    
    if "registry = CollectorRegistry()" in content:
        print(f"✅ Métriques déjà définies dans {main_file}")
        return True
    
    # Template de métriques
    metrics_template = f'''
# Prometheus metrics
registry = CollectorRegistry()

# Métriques HTTP
http_requests = Counter(
    '{service_name.lower().replace("-", "_")}_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration = Histogram(
    '{service_name.lower().replace("-", "_")}_http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    registry=registry
)

# Métriques de performance
memory_usage = Gauge(
    '{service_name.lower().replace("-", "_")}_memory_usage_bytes',
    'Memory usage in bytes',
    registry=registry
)

# Métriques d'erreur
errors = Counter(
    '{service_name.lower().replace("-", "_")}_errors_total',
    'Total errors',
    ['error_type'],
    registry=registry
)
'''
    
    # Trouver où insérer (après l'initialisation FastAPI)
    lines = content.split('\n')
    app_line = -1
    
    for i, line in enumerate(lines):
        if "app = FastAPI(" in line:
            app_line = i
            break
    
    if app_line == -1:
        print(f"❌ Initialisation FastAPI non trouvée dans {main_file}")
        return False
    
    # Trouver la fin de l'initialisation FastAPI
    end_app_line = app_line
    paren_count = 0
    in_app_init = False
    
    for i in range(app_line, len(lines)):
        line = lines[i]
        if "app = FastAPI(" in line:
            in_app_init = True
        
        if in_app_init:
            paren_count += line.count('(') - line.count(')')
            end_app_line = i
            if paren_count == 0:
                break
    
    # Insérer les métriques après l'initialisation FastAPI
    metrics_lines = metrics_template.strip().split('\n')
    for i, metric_line in enumerate(reversed(metrics_lines)):
        lines.insert(end_app_line + 1, metric_line)
    
    main_file.write_text('\n'.join(lines))
    print(f"✅ Ajouté définitions de métriques à {main_file}")
    return True

def add_metrics_endpoint(main_file):
    """Ajoute l'endpoint /metrics"""
    content = main_file.read_text()
    
    if 'def get_metrics()' in content:
        print(f"✅ Endpoint /metrics déjà présent dans {main_file}")
        return True
    
    metrics_endpoint = '''
@app.get("/metrics")
async def get_metrics():
    """Endpoint Prometheus pour les métriques"""
    # Mise à jour des métriques système
    process = psutil.Process()
    memory_usage.set(process.memory_info().rss)
    
    return Response(
        generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST
    )
'''
    
    # Trouver l'endpoint /health pour insérer après
    lines = content.split('\n')
    health_end = -1
    
    for i, line in enumerate(lines):
        if '/health' in line and '@app.get' in line:
            # Trouver la fin de cette fonction
            for j in range(i + 1, len(lines)):
                if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                    health_end = j - 1
                    break
            break
    
    if health_end == -1:
        # Ajouter à la fin du fichier
        content += metrics_endpoint
    else:
        # Insérer après l'endpoint health
        endpoint_lines = metrics_endpoint.strip().split('\n')
        for i, endpoint_line in enumerate(reversed(endpoint_lines)):
            lines.insert(health_end + 1, endpoint_line)
        content = '\n'.join(lines)
    
    main_file.write_text(content)
    print(f"✅ Ajouté endpoint /metrics à {main_file}")
    return True

def process_service(service_path, service_name):
    """Traite un service pour ajouter l'instrumentation Prometheus"""
    print(f"\n🔧 Traitement du service: {service_name}")
    
    main_file = service_path / "main.py"
    
    # Étapes d'instrumentation
    steps = [
        ("Ajout dependencies", lambda: add_prometheus_to_requirements(service_path)),
        ("Ajout imports", lambda: add_prometheus_imports(main_file)),
        ("Ajout métriques", lambda: add_metrics_definitions(main_file, service_name)),
        ("Ajout endpoint", lambda: add_metrics_endpoint(main_file))
    ]
    
    success = True
    for step_name, step_func in steps:
        print(f"  ⏳ {step_name}...")
        if not step_func():
            print(f"  ❌ Échec: {step_name}")
            success = False
        else:
            print(f"  ✅ {step_name}")
    
    return success

def main():
    """Fonction principale"""
    print("🔍 JARVIS AI 2025 - Ajout automatique d'instrumentation Prometheus")
    print("=" * 70)
    
    # Services à instrumenter
    services = [
        "terminal-service",
        "mcp-gateway", 
        "autocomplete-service"
    ]
    
    base_path = Path("services")
    
    if not base_path.exists():
        print("❌ Répertoire 'services' non trouvé")
        sys.exit(1)
    
    success_count = 0
    
    for service in services:
        service_path = base_path / service
        
        if not service_path.exists():
            print(f"⚠️ Service {service} non trouvé dans {service_path}")
            continue
        
        if process_service(service_path, service):
            success_count += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Instrumentation terminée: {success_count}/{len(services)} services traités")
    
    if success_count == len(services):
        print("🎉 Tous les services ont été instrumentés avec succès!")
        print("\n📋 Prochaines étapes:")
        print("1. Reconstruire les images Docker des services modifiés")
        print("2. Redémarrer les services avec docker-compose")
        print("3. Vérifier les métriques sur http://localhost:9090")
        print("4. Consulter les dashboards Grafana sur http://localhost:3001")
    else:
        print("⚠️ Certains services n'ont pas pu être traités complètement")
        print("Vérifiez les messages d'erreur ci-dessus")

if __name__ == "__main__":
    main()