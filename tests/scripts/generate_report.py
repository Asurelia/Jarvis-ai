#!/usr/bin/env python3
"""
📊 Générateur de rapports consolidés pour les tests JARVIS
Combine tous les résultats de tests en un rapport HTML unifié
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import xml.etree.ElementTree as ET
from dataclasses import dataclass

# Configuration HTML
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧪 JARVIS - Rapport de Tests Consolidé</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0d1421 0%, #1a252f 100%);
            color: #e0e0e0;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(0, 255, 65, 0.1);
            border-radius: 15px;
            border: 1px solid #00ff41;
        }
        
        .header h1 {
            font-size: 2.5rem;
            color: #00ff41;
            margin-bottom: 10px;
        }
        
        .header .timestamp {
            color: #888;
            font-size: 1.1rem;
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .summary-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid;
            transition: transform 0.3s ease;
        }
        
        .summary-card:hover {
            transform: translateY(-5px);
        }
        
        .summary-card.success { border-color: #28a745; }
        .summary-card.warning { border-color: #ffc107; }
        .summary-card.error { border-color: #dc3545; }
        .summary-card.info { border-color: #17a2b8; }
        
        .summary-card h3 {
            font-size: 1.2rem;
            margin-bottom: 10px;
        }
        
        .summary-card .value {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .summary-card .label {
            color: #aaa;
            font-size: 0.9rem;
        }
        
        .section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 30px;
        }
        
        .section h2 {
            color: #00ff41;
            margin-bottom: 20px;
            font-size: 1.5rem;
            border-bottom: 2px solid #00ff41;
            padding-bottom: 10px;
        }
        
        .test-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }
        
        .test-table th,
        .test-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .test-table th {
            background: rgba(0, 255, 65, 0.1);
            font-weight: bold;
        }
        
        .status-pass { color: #28a745; }
        .status-fail { color: #dc3545; }
        .status-skip { color: #ffc107; }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }
        
        .progress-success { background: #28a745; }
        .progress-warning { background: #ffc107; }
        .progress-error { background: #dc3545; }
        
        .chart-container {
            margin: 20px 0;
            height: 200px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-style: italic;
            color: #666;
        }
        
        .footer {
            text-align: center;
            margin-top: 50px;
            padding: 20px;
            color: #666;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .error-details {
            background: rgba(220, 53, 69, 0.1);
            border: 1px solid #dc3545;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.9rem;
        }
        
        .coverage-bar {
            display: flex;
            height: 10px;
            border-radius: 5px;
            overflow: hidden;
            margin: 5px 0;
        }
        
        .coverage-covered { background: #28a745; }
        .coverage-uncovered { background: #dc3545; }
        
        @media (max-width: 768px) {
            .summary-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header class="header">
            <h1>🧪 JARVIS - Rapport de Tests</h1>
            <div class="timestamp">Généré le {timestamp}</div>
        </header>
        
        {summary_cards}
        
        {sections}
        
        <footer class="footer">
            <p>🤖 Généré automatiquement par le système de tests JARVIS</p>
            <p>Pour plus d'informations, consultez les logs détaillés.</p>
        </footer>
    </div>
</body>
</html>
"""

@dataclass
class TestResult:
    name: str
    status: str
    duration: float = 0.0
    error: str = None

@dataclass
class TestSuite:
    name: str
    tests: List[TestResult]
    total_time: float = 0.0
    
    @property
    def passed(self) -> int:
        return len([t for t in self.tests if t.status == 'pass'])
    
    @property
    def failed(self) -> int:
        return len([t for t in self.tests if t.status == 'fail'])
    
    @property
    def skipped(self) -> int:
        return len([t for t in self.tests if t.status == 'skip'])
    
    @property
    def total(self) -> int:
        return len(self.tests)
    
    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return (self.passed / self.total) * 100

class TestReportGenerator:
    def __init__(self, results_dir: Path, coverage_dir: Path = None):
        self.results_dir = Path(results_dir)
        self.coverage_dir = Path(coverage_dir) if coverage_dir else None
        self.test_suites: List[TestSuite] = []
        self.performance_data = {}
        self.coverage_data = {}
        
    def parse_pytest_xml(self, xml_file: Path) -> TestSuite:
        """Parse un fichier XML de résultats pytest"""
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            suite_name = root.get('name', xml_file.stem)
            tests = []
            
            for testcase in root.findall('.//testcase'):
                name = f"{testcase.get('classname', '')}.{testcase.get('name', '')}"
                duration = float(testcase.get('time', 0))
                
                # Déterminer le status
                if testcase.find('failure') is not None:
                    status = 'fail'
                    error = testcase.find('failure').text
                elif testcase.find('error') is not None:
                    status = 'fail'
                    error = testcase.find('error').text
                elif testcase.find('skipped') is not None:
                    status = 'skip'
                    error = None
                else:
                    status = 'pass'
                    error = None
                
                tests.append(TestResult(name, status, duration, error))
            
            total_time = float(root.get('time', 0))
            return TestSuite(suite_name, tests, total_time)
            
        except Exception as e:
            print(f"Erreur lors du parsing de {xml_file}: {e}")
            return TestSuite(xml_file.stem, [], 0.0)
    
    def parse_jest_json(self, json_file: Path) -> TestSuite:
        """Parse un fichier JSON de résultats Jest"""
        try:
            with open(json_file) as f:
                data = json.load(f)
            
            suite_name = "Tests JavaScript"
            tests = []
            
            for test_result in data.get('testResults', []):
                for assertion in test_result.get('assertionResults', []):
                    name = assertion.get('fullName', '')
                    duration = assertion.get('duration', 0) / 1000  # Convert ms to s
                    status = 'pass' if assertion.get('status') == 'passed' else 'fail'
                    error = assertion.get('failureMessages', [None])[0] if status == 'fail' else None
                    
                    tests.append(TestResult(name, status, duration, error))
            
            return TestSuite(suite_name, tests, data.get('totalTime', 0) / 1000)
            
        except Exception as e:
            print(f"Erreur lors du parsing de {json_file}: {e}")
            return TestSuite("Tests JavaScript", [], 0.0)
    
    def parse_k6_json(self, json_file: Path):
        """Parse les résultats de performance K6"""
        try:
            with open(json_file) as f:
                data = json.load(f)
            
            metrics = data.get('metrics', {})
            self.performance_data = {
                'http_reqs': metrics.get('http_reqs', {}).get('count', 0),
                'http_req_duration_avg': metrics.get('http_req_duration', {}).get('avg', 0),
                'http_req_duration_p95': metrics.get('http_req_duration', {}).get('p95', 0),
                'http_req_failed_rate': metrics.get('http_req_failed', {}).get('rate', 0) * 100,
                'vus_max': metrics.get('vus_max', {}).get('value', 0),
            }
            
        except Exception as e:
            print(f"Erreur lors du parsing de {json_file}: {e}")
    
    def parse_coverage_json(self, json_file: Path):
        """Parse les données de couverture de code"""
        try:
            with open(json_file) as f:
                data = json.load(f)
            
            # Format coverage.py
            if 'totals' in data:
                totals = data['totals']
                self.coverage_data = {
                    'lines_covered': totals.get('covered_lines', 0),
                    'lines_total': totals.get('num_statements', 0),
                    'coverage_percent': totals.get('percent_covered', 0),
                    'branches_covered': totals.get('covered_branches', 0),
                    'branches_total': totals.get('num_branches', 0),
                }
            
        except Exception as e:
            print(f"Erreur lors du parsing de {json_file}: {e}")
    
    def collect_results(self):
        """Collecte tous les résultats de tests"""
        if not self.results_dir.exists():
            print(f"Répertoire de résultats non trouvé: {self.results_dir}")
            return
        
        # Parser les fichiers XML (pytest)
        for xml_file in self.results_dir.glob("**/*.xml"):
            if "junit" in xml_file.name.lower() or "pytest" in xml_file.name.lower():
                suite = self.parse_pytest_xml(xml_file)
                self.test_suites.append(suite)
        
        # Parser les fichiers JSON (Jest, K6, etc.)
        for json_file in self.results_dir.glob("**/*.json"):
            if "jest" in json_file.name.lower():
                suite = self.parse_jest_json(json_file)
                self.test_suites.append(suite)
            elif "performance" in json_file.name.lower() or "k6" in json_file.name.lower():
                self.parse_k6_json(json_file)
            elif "coverage" in json_file.name.lower():
                self.parse_coverage_json(json_file)
        
        # Parser la couverture si disponible
        if self.coverage_dir and self.coverage_dir.exists():
            coverage_json = self.coverage_dir / "coverage.json"
            if coverage_json.exists():
                self.parse_coverage_json(coverage_json)
    
    def generate_summary_cards(self) -> str:
        """Génère les cartes de résumé"""
        total_tests = sum(suite.total for suite in self.test_suites)
        total_passed = sum(suite.passed for suite in self.test_suites)
        total_failed = sum(suite.failed for suite in self.test_suites)
        total_skipped = sum(suite.skipped for suite in self.test_suites)
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        cards = f"""
        <div class="summary-grid">
            <div class="summary-card {'success' if success_rate > 90 else 'warning' if success_rate > 70 else 'error'}">
                <h3>Taux de Réussite</h3>
                <div class="value">{success_rate:.1f}%</div>
                <div class="label">{total_passed}/{total_tests} tests réussis</div>
            </div>
            
            <div class="summary-card info">
                <h3>Total Tests</h3>
                <div class="value">{total_tests}</div>
                <div class="label">Across {len(self.test_suites)} test suites</div>
            </div>
            
            <div class="summary-card {'success' if total_failed == 0 else 'error'}">
                <h3>Échecs</h3>
                <div class="value">{total_failed}</div>
                <div class="label">Tests échoués</div>
            </div>
            
            <div class="summary-card warning">
                <h3>Ignorés</h3>
                <div class="value">{total_skipped}</div>
                <div class="label">Tests ignorés</div>
            </div>
        </div>
        """
        
        # Ajouter les métriques de performance si disponibles
        if self.performance_data:
            perf_card = f"""
            <div class="summary-card info">
                <h3>Performance</h3>
                <div class="value">{self.performance_data.get('http_req_duration_p95', 0):.0f}ms</div>
                <div class="label">P95 Response Time</div>
            </div>
            """
            cards = cards.replace('</div>', perf_card + '</div>', 1)
        
        # Ajouter la couverture si disponible
        if self.coverage_data:
            coverage_pct = self.coverage_data.get('coverage_percent', 0)
            coverage_card = f"""
            <div class="summary-card {'success' if coverage_pct > 80 else 'warning' if coverage_pct > 60 else 'error'}">
                <h3>Couverture</h3>
                <div class="value">{coverage_pct:.1f}%</div>
                <div class="label">Code Coverage</div>
            </div>
            """
            cards = cards.replace('</div>', coverage_card + '</div>', 1)
        
        return cards
    
    def generate_sections(self) -> str:
        """Génère les sections détaillées"""
        sections = ""
        
        # Section des suites de tests
        if self.test_suites:
            sections += """
            <section class="section">
                <h2>📋 Résultats des Tests par Suite</h2>
            """
            
            for suite in self.test_suites:
                success_rate = suite.success_rate
                sections += f"""
                <h3>{suite.name}</h3>
                <div class="progress-bar">
                    <div class="progress-fill progress-{'success' if success_rate > 90 else 'warning' if success_rate > 70 else 'error'}" 
                         style="width: {success_rate}%"></div>
                </div>
                <p>
                    ✅ {suite.passed} réussis | 
                    ❌ {suite.failed} échoués | 
                    ⚠️ {suite.skipped} ignorés | 
                    ⏱️ {suite.total_time:.2f}s
                </p>
                """
                
                # Afficher les tests échoués
                failed_tests = [t for t in suite.tests if t.status == 'fail']
                if failed_tests:
                    sections += '<h4>Tests échoués:</h4>'
                    for test in failed_tests[:5]:  # Limiter à 5
                        sections += f"""
                        <div class="error-details">
                            <strong>{test.name}</strong><br>
                            {test.error[:200] if test.error else 'Erreur non spécifiée'}...
                        </div>
                        """
            
            sections += "</section>"
        
        # Section performance
        if self.performance_data:
            sections += f"""
            <section class="section">
                <h2>⚡ Métriques de Performance</h2>
                <div class="test-table">
                    <table>
                        <tr><th>Métrique</th><th>Valeur</th></tr>
                        <tr><td>Total Requests</td><td>{self.performance_data.get('http_reqs', 0)}</td></tr>
                        <tr><td>Average Response Time</td><td>{self.performance_data.get('http_req_duration_avg', 0):.2f}ms</td></tr>
                        <tr><td>95th Percentile</td><td>{self.performance_data.get('http_req_duration_p95', 0):.2f}ms</td></tr>
                        <tr><td>Failed Requests</td><td>{self.performance_data.get('http_req_failed_rate', 0):.2f}%</td></tr>
                        <tr><td>Max Virtual Users</td><td>{self.performance_data.get('vus_max', 0)}</td></tr>
                    </table>
                </div>
            </section>
            """
        
        # Section couverture
        if self.coverage_data:
            coverage_pct = self.coverage_data.get('coverage_percent', 0)
            lines_covered = self.coverage_data.get('lines_covered', 0)
            lines_total = self.coverage_data.get('lines_total', 0)
            
            sections += f"""
            <section class="section">
                <h2>📊 Couverture de Code</h2>
                <div class="coverage-bar">
                    <div class="coverage-covered" style="width: {coverage_pct}%"></div>
                    <div class="coverage-uncovered" style="width: {100-coverage_pct}%"></div>
                </div>
                <p>
                    {lines_covered} / {lines_total} lignes couvertes ({coverage_pct:.1f}%)
                </p>
            </section>
            """
        
        return sections
    
    def generate_report(self, output_file: Path):
        """Génère le rapport HTML final"""
        self.collect_results()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary_cards = self.generate_summary_cards()
        sections = self.generate_sections()
        
        html_content = HTML_TEMPLATE.format(
            timestamp=timestamp,
            summary_cards=summary_cards,
            sections=sections
        )
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Rapport généré: {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description="Génère un rapport consolidé des tests JARVIS")
    parser.add_argument('--results', required=True, help="Répertoire contenant les résultats de tests")
    parser.add_argument('--coverage', help="Répertoire contenant les données de couverture")
    parser.add_argument('--output', required=True, help="Fichier HTML de sortie")
    
    args = parser.parse_args()
    
    generator = TestReportGenerator(
        results_dir=Path(args.results),
        coverage_dir=Path(args.coverage) if args.coverage else None
    )
    
    output_file = Path(args.output)
    report_file = generator.generate_report(output_file)
    
    print(f"🎉 Rapport consolidé généré avec succès !")
    print(f"📄 Fichier: file://{report_file.absolute()}")

if __name__ == "__main__":
    main()