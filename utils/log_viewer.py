#!/usr/bin/env python3
"""
📊 Visualiseur de logs JARVIS
Interface en ligne de commande pour analyser et visualiser les logs
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
import time

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from config.logging_config import jarvis_logger

class LogAnalyzer:
    """Analyseur de logs JARVIS"""
    
    def __init__(self, log_directory: str = None):
        self.log_dir = Path(log_directory) if log_directory else Path(settings.log_file_path).parent
        self.stats = defaultdict(int)
        
    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse une ligne de log"""
        # Pattern pour les logs JARVIS
        pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s+ \| (.+?) - (.+)"
        
        match = re.match(pattern, line)
        if not match:
            return None
        
        timestamp_str, level, location, message = match.groups()
        
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return None
        
        # Extraire module:fonction:ligne
        location_parts = location.split(":")
        if len(location_parts) >= 3:
            module = location_parts[0]
            function = location_parts[1]
            line_num = location_parts[2]
        else:
            module = location
            function = ""
            line_num = ""
        
        return {
            "timestamp": timestamp,
            "level": level,
            "module": module,
            "function": function,
            "line": line_num,
            "message": message,
            "raw": line
        }
    
    def analyze_log_file(self, log_file: Path) -> Dict[str, Any]:
        """Analyse un fichier de log"""
        if not log_file.exists():
            return {"error": f"Fichier non trouvé: {log_file}"}
        
        analysis = {
            "file": str(log_file),
            "total_lines": 0,
            "parsed_lines": 0,
            "levels": Counter(),
            "modules": Counter(),
            "errors": [],
            "timeline": defaultdict(int),
            "performance": [],
            "first_entry": None,
            "last_entry": None
        }
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    analysis["total_lines"] += 1
                    line = line.strip()
                    
                    if not line:
                        continue
                    
                    parsed = self.parse_log_line(line)
                    if parsed:
                        analysis["parsed_lines"] += 1
                        
                        # Statistiques de base
                        analysis["levels"][parsed["level"]] += 1
                        analysis["modules"][parsed["module"]] += 1
                        
                        # Timeline (par heure)
                        hour_key = parsed["timestamp"].strftime("%Y-%m-%d %H:00")
                        analysis["timeline"][hour_key] += 1
                        
                        # Première et dernière entrée
                        if not analysis["first_entry"]:
                            analysis["first_entry"] = parsed["timestamp"]
                        analysis["last_entry"] = parsed["timestamp"]
                        
                        # Collecter les erreurs
                        if parsed["level"] in ["ERROR", "CRITICAL"]:
                            analysis["errors"].append({
                                "timestamp": parsed["timestamp"].isoformat(),
                                "module": parsed["module"],
                                "message": parsed["message"]
                            })
                        
                        # Détecter les logs de performance
                        if "duration" in parsed["message"].lower() or "ms" in parsed["message"] or "took" in parsed["message"].lower():
                            analysis["performance"].append({
                                "timestamp": parsed["timestamp"].isoformat(),
                                "module": parsed["module"],
                                "message": parsed["message"]
                            })
        
        except Exception as e:
            analysis["error"] = str(e)
        
        return analysis
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Génère un rapport de résumé de tous les logs"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "log_directory": str(self.log_dir),
            "files_analyzed": 0,
            "total_entries": 0,
            "date_range": {},
            "levels_summary": Counter(),
            "modules_summary": Counter(),
            "error_summary": [],
            "top_errors": [],
            "activity_timeline": defaultdict(int),
            "file_details": {}
        }
        
        if not self.log_dir.exists():
            report["error"] = "Répertoire de logs non trouvé"
            return report
        
        all_timestamps = []
        all_errors = []
        
        # Analyser tous les fichiers .log
        for log_file in self.log_dir.glob("*.log"):
            analysis = self.analyze_log_file(log_file)
            
            if "error" not in analysis:
                report["files_analyzed"] += 1
                report["total_entries"] += analysis["parsed_lines"]
                
                # Agrégation des statistiques
                report["levels_summary"].update(analysis["levels"])
                report["modules_summary"].update(analysis["modules"])
                
                # Timeline globale
                for hour, count in analysis["timeline"].items():
                    report["activity_timeline"][hour] += count
                
                # Erreurs
                all_errors.extend(analysis["errors"])
                
                # Timestamps pour la plage de dates
                if analysis["first_entry"]:
                    all_timestamps.append(analysis["first_entry"])
                if analysis["last_entry"]:
                    all_timestamps.append(analysis["last_entry"])
                
                # Détails du fichier
                report["file_details"][log_file.name] = {
                    "lines": analysis["total_lines"],
                    "parsed": analysis["parsed_lines"],
                    "levels": dict(analysis["levels"]),
                    "errors_count": len(analysis["errors"])
                }
        
        # Plage de dates
        if all_timestamps:
            report["date_range"] = {
                "start": min(all_timestamps).isoformat(),
                "end": max(all_timestamps).isoformat(),
                "duration_hours": (max(all_timestamps) - min(all_timestamps)).total_seconds() / 3600
            }
        
        # Top erreurs
        error_messages = [error["message"] for error in all_errors]
        error_counts = Counter(error_messages)
        report["top_errors"] = [
            {"message": msg, "count": count}
            for msg, count in error_counts.most_common(10)
        ]
        
        report["error_summary"] = all_errors[-20:]  # 20 dernières erreurs
        
        return report
    
    def search_logs(self, query: str, level: str = None, 
                   module: str = None, start_time: datetime = None, 
                   end_time: datetime = None, max_results: int = 100) -> List[Dict[str, Any]]:
        """Recherche dans les logs"""
        results = []
        query_lower = query.lower()
        
        for log_file in self.log_dir.glob("*.log"):
            if len(results) >= max_results:
                break
                
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if len(results) >= max_results:
                            break
                            
                        parsed = self.parse_log_line(line.strip())
                        if not parsed:
                            continue
                        
                        # Filtres
                        if level and parsed["level"] != level.upper():
                            continue
                        
                        if module and module.lower() not in parsed["module"].lower():
                            continue
                        
                        if start_time and parsed["timestamp"] < start_time:
                            continue
                        
                        if end_time and parsed["timestamp"] > end_time:
                            continue
                        
                        # Recherche dans le message
                        if query_lower in parsed["message"].lower():
                            results.append({
                                "file": log_file.name,
                                "timestamp": parsed["timestamp"].isoformat(),
                                "level": parsed["level"],
                                "module": parsed["module"],
                                "message": parsed["message"]
                            })
            
            except Exception as e:
                continue
        
        return results
    
    def get_activity_chart(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Génère un graphique d'activité"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # Créer des slots horaires
        hourly_activity = defaultdict(lambda: {"total": 0, "errors": 0, "warnings": 0})
        
        for log_file in self.log_dir.glob("*.log"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        parsed = self.parse_log_line(line.strip())
                        if not parsed:
                            continue
                        
                        if start_time <= parsed["timestamp"] <= end_time:
                            hour_key = parsed["timestamp"].strftime("%Y-%m-%d %H:00")
                            hourly_activity[hour_key]["total"] += 1
                            
                            if parsed["level"] == "ERROR":
                                hourly_activity[hour_key]["errors"] += 1
                            elif parsed["level"] == "WARNING":
                                hourly_activity[hour_key]["warnings"] += 1
            
            except Exception:
                continue
        
        # Convertir en liste ordonnée
        chart_data = []
        current_time = start_time.replace(minute=0, second=0, microsecond=0)
        
        while current_time <= end_time:
            hour_key = current_time.strftime("%Y-%m-%d %H:00")
            data = hourly_activity.get(hour_key, {"total": 0, "errors": 0, "warnings": 0})
            
            chart_data.append({
                "hour": hour_key,
                "timestamp": current_time.isoformat(),
                "total": data["total"],
                "errors": data["errors"],
                "warnings": data["warnings"]
            })
            
            current_time += timedelta(hours=1)
        
        return chart_data

def print_analysis_report(report: Dict[str, Any]):
    """Affiche un rapport d'analyse formaté"""
    print("="*60)
    print("📊 RAPPORT D'ANALYSE DES LOGS JARVIS")
    print("="*60)
    
    if "error" in report:
        print(f"❌ Erreur: {report['error']}")
        return
    
    # Informations générales
    print(f"📁 Répertoire: {report['log_directory']}")
    print(f"📄 Fichiers analysés: {report['files_analyzed']}")
    print(f"📝 Entrées totales: {report['total_entries']:,}")
    
    # Plage de dates
    if report.get("date_range"):
        dr = report["date_range"]
        print(f"📅 Période: {dr['start']} → {dr['end']}")
        print(f"⏱️  Durée: {dr['duration_hours']:.1f} heures")
    
    # Niveaux de logs
    print("\\n📊 Répartition par niveau:")
    for level, count in report["levels_summary"].most_common():
        percentage = (count / report["total_entries"]) * 100
        print(f"  {level:<8}: {count:>6,} ({percentage:5.1f}%)")
    
    # Modules les plus actifs
    print("\\n🏗️ Modules les plus actifs:")
    for module, count in report["modules_summary"].most_common(10):
        percentage = (count / report["total_entries"]) * 100
        print(f"  {module:<20}: {count:>6,} ({percentage:5.1f}%)")
    
    # Erreurs principales
    if report["top_errors"]:
        print("\\n❌ Erreurs les plus fréquentes:")
        for error in report["top_errors"][:5]:
            print(f"  [{error['count']:>3}x] {error['message'][:60]}...")
    
    # Activité récente
    recent_activity = sorted(
        report["activity_timeline"].items(),
        key=lambda x: x[0], reverse=True
    )[:5]
    
    if recent_activity:
        print("\\n📈 Activité récente (par heure):")
        for hour, count in recent_activity:
            print(f"  {hour}: {count:>4} entrées")

def main():
    """Interface en ligne de commande"""
    parser = argparse.ArgumentParser(description="Analyseur de logs JARVIS")
    parser.add_argument("--directory", "-d", help="Répertoire des logs")
    parser.add_argument("--summary", "-s", action="store_true", help="Rapport de résumé")
    parser.add_argument("--search", help="Rechercher dans les logs")
    parser.add_argument("--level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="Filtrer par niveau")
    parser.add_argument("--module", help="Filtrer par module")
    parser.add_argument("--hours", type=int, default=24, help="Heures à analyser (défaut: 24)")
    parser.add_argument("--chart", action="store_true", help="Graphique d'activité")
    parser.add_argument("--export", help="Exporter vers fichier JSON")
    parser.add_argument("--stats", action="store_true", help="Statistiques des fichiers de logs")
    
    args = parser.parse_args()
    
    # Initialiser l'analyseur
    analyzer = LogAnalyzer(args.directory)
    
    if args.stats:
        # Afficher les statistiques des fichiers
        stats = jarvis_logger.get_log_stats()
        print("📁 Statistiques des fichiers de logs:")
        print(json.dumps(stats, indent=2, default=str))
        
    elif args.summary:
        # Rapport de résumé
        report = analyzer.generate_summary_report()
        print_analysis_report(report)
        
        if args.export:
            with open(args.export, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\\n💾 Rapport exporté vers: {args.export}")
    
    elif args.search:
        # Recherche dans les logs
        results = analyzer.search_logs(
            query=args.search,
            level=args.level,
            module=args.module,
            max_results=50
        )
        
        print(f"🔍 Résultats de recherche pour '{args.search}' ({len(results)} trouvés):")
        print("-" * 80)
        
        for result in results:
            print(f"[{result['timestamp']}] {result['level']:<8} | {result['module']:<15} | {result['message']}")
    
    elif args.chart:
        # Graphique d'activité
        chart_data = analyzer.get_activity_chart(args.hours)
        
        print(f"📈 Activité des logs ({args.hours} dernières heures):")
        print("-" * 60)
        print(f"{'Heure':<17} | {'Total':>6} | {'Erreurs':>8} | {'Warn':>6}")
        print("-" * 60)
        
        for data in chart_data[-24:]:  # 24 dernières heures
            hour = data['hour'].split()[1]  # Juste l'heure
            total = data['total']
            errors = data['errors']
            warnings = data['warnings']
            
            # Graphique ASCII simple
            bar = '█' * min(total // 10, 20)
            
            print(f"{hour:<17} | {total:>6} | {errors:>8} | {warnings:>6} {bar}")
    
    else:
        # Mode par défaut: résumé rapide
        print("📝 Logs JARVIS - Résumé rapide")
        
        stats = jarvis_logger.get_log_stats()
        print(f"📁 Répertoire: {stats.get('log_directory', 'Non trouvé')}")
        print(f"📄 Fichiers: {len(stats.get('files', {}))}")
        print(f"💾 Taille totale: {stats.get('total_size_mb', 0):.2f} MB")
        
        # Dernières lignes
        recent_logs = jarvis_logger.get_recent_logs(lines=10)
        if recent_logs:
            print("\\n📋 Dernières entrées:")
            for log_line in recent_logs:
                print(f"  {log_line}")

if __name__ == "__main__":
    main()