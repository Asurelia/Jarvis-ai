#!/usr/bin/env python3
"""
JARVIS MCP Server - Model Context Protocol Implementation
Provides intelligent project navigation and search capabilities
"""

import json
import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProjectContext:
    """Represents the current context and memory of the JARVIS project"""
    project_root: Path
    memory_file: Path
    memory_data: Dict[str, Any]
    last_search: Optional[str] = None
    search_history: List[str] = None
    
    def __post_init__(self):
        if self.search_history is None:
            self.search_history = []

class JarvisMCPServer:
    """
    MCP Server for JARVIS AI Project
    Provides intelligent search, navigation, and context management
    """
    
    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.memory_file = self.project_root / "JARVIS_PROJECT_MEMORY.json"
        self.context = self._load_context()
        
    def _load_context(self) -> ProjectContext:
        """Load project memory and context"""
        if self.memory_file.exists():
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                memory_data = json.load(f)
        else:
            memory_data = {}
            
        return ProjectContext(
            project_root=self.project_root,
            memory_file=self.memory_file,
            memory_data=memory_data
        )
    
    def update_memory(self, updates: Dict[str, Any]):
        """Update and persist project memory"""
        self.context.memory_data.update(updates)
        self.context.memory_data['last_updated'] = datetime.now().isoformat()
        
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.context.memory_data, f, indent=2)
    
    # MCP Protocol Methods
    
    async def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific service"""
        services = self.context.memory_data.get('structure', {}).get('core_services', {})
        
        if service_name in services:
            service_info = services[service_name]
            # Add real-time status if possible
            service_info['status'] = await self._check_service_health(service_name)
            return service_info
        
        return {"error": f"Service {service_name} not found"}
    
    async def find_related_files(self, query: str) -> List[str]:
        """Find files related to a query using project memory"""
        related_files = []
        query_lower = query.lower()
        
        # Search in shortcuts
        shortcuts = self.context.memory_data.get('search_shortcuts', {})
        for key, path in shortcuts.items():
            if query_lower in key.lower():
                related_files.append(path)
        
        # Search in service key files
        services = self.context.memory_data.get('structure', {}).get('core_services', {})
        for service_name, service_data in services.items():
            if query_lower in service_name.lower():
                if 'key_files' in service_data:
                    base_path = service_data.get('path', '')
                    related_files.extend([f"{base_path}{f}" for f in service_data['key_files']])
        
        # Search in core modules
        modules = self.context.memory_data.get('structure', {}).get('core_modules', {})
        for module_name, module_data in modules.items():
            if query_lower in module_name.lower():
                base_path = module_data.get('path', '')
                if 'modules' in module_data:
                    related_files.extend([f"{base_path}{f}" for f in module_data['modules']])
        
        # Update search history
        self.context.search_history.append(query)
        self.context.last_search = query
        
        return list(set(related_files))  # Remove duplicates
    
    async def get_security_issues(self, severity: str = None) -> Dict[str, List[str]]:
        """Get security issues from memory"""
        issues = self.context.memory_data.get('security_issues', {})
        
        if severity:
            return {severity: issues.get(severity, [])}
        return issues
    
    async def get_cleanup_targets(self, safe_only: bool = True) -> Dict[str, List[str]]:
        """Get files/folders to clean up"""
        targets = self.context.memory_data.get('cleanup_targets', {})
        
        if safe_only:
            return {"safe_to_delete": targets.get('safe_to_delete', [])}
        return targets
    
    async def get_integration_points(self) -> Dict[str, Any]:
        """Get external integration points and APIs"""
        return self.context.memory_data.get('integration_points', {})
    
    async def get_recommendations(self, priority: str = "immediate") -> List[str]:
        """Get recommendations by priority"""
        recs = self.context.memory_data.get('recommendations', {})
        return recs.get(priority, [])
    
    async def navigate_to_component(self, component_type: str) -> Dict[str, Any]:
        """Navigate to a specific component type"""
        navigation_map = {
            "api": "services/brain-api/",
            "ui": "ui/src/",
            "core": "core/",
            "tests": "tests/",
            "docker": "docker-compose.yml",
            "database": "database/",
            "monitoring": "monitoring/"
        }
        
        if component_type in navigation_map:
            path = navigation_map[component_type]
            full_path = self.project_root / path
            
            return {
                "path": str(path),
                "full_path": str(full_path),
                "exists": full_path.exists(),
                "related": await self.find_related_files(component_type)
            }
        
        return {"error": f"Unknown component type: {component_type}"}
    
    async def analyze_complexity(self, file_path: str = None) -> Dict[str, Any]:
        """Analyze complexity of files or components"""
        if file_path:
            # Analyze specific file
            full_path = self.project_root / file_path
            if full_path.exists() and full_path.suffix == '.py':
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                return {
                    "file": file_path,
                    "lines": len(lines),
                    "functions": sum(1 for line in lines if line.strip().startswith('def ')),
                    "classes": sum(1 for line in lines if line.strip().startswith('class ')),
                    "complexity_note": self._get_complexity_note(len(lines))
                }
        else:
            # Return known complexity issues
            return self.context.memory_data.get('performance_bottlenecks', {})
    
    def _get_complexity_note(self, line_count: int) -> str:
        """Get complexity assessment based on line count"""
        if line_count < 100:
            return "Low complexity"
        elif line_count < 300:
            return "Medium complexity"
        elif line_count < 500:
            return "High complexity - consider refactoring"
        else:
            return "Very high complexity - refactoring recommended"
    
    async def _check_service_health(self, service_name: str) -> str:
        """Check if a service is running (simplified)"""
        # This would normally check actual service health
        # For now, return a placeholder
        return "unknown"
    
    async def search_pattern(self, pattern: str, file_type: str = None) -> List[Dict[str, Any]]:
        """Search for patterns in the codebase"""
        results = []
        search_paths = []
        
        if file_type == "python":
            search_paths = ["core/", "services/", "tools/", "database/"]
            pattern_glob = "**/*.py"
        elif file_type == "javascript":
            search_paths = ["ui/src/"]
            pattern_glob = "**/*.js"
        elif file_type == "jsx":
            search_paths = ["ui/src/"]
            pattern_glob = "**/*.jsx"
        else:
            search_paths = ["."]
            pattern_glob = "**/*"
        
        for search_path in search_paths:
            base_path = self.project_root / search_path
            if base_path.exists():
                for file_path in base_path.glob(pattern_glob):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if pattern.lower() in content.lower():
                                    results.append({
                                        "file": str(file_path.relative_to(self.project_root)),
                                        "matches": content.lower().count(pattern.lower())
                                    })
                        except:
                            pass  # Skip files that can't be read
        
        return results[:20]  # Limit to 20 results

# CLI Interface for testing
async def main():
    """Test the MCP server functionality"""
    server = JarvisMCPServer()
    
    print("JARVIS MCP Server initialized")
    print(f"Project root: {server.project_root}")
    print(f"Memory file: {server.memory_file}")
    
    # Test some functions
    print("\n--- Service Info ---")
    info = await server.get_service_info("brain-api")
    print(json.dumps(info, indent=2))
    
    print("\n--- Related Files for 'voice' ---")
    files = await server.find_related_files("voice")
    for f in files:
        print(f"  - {f}")
    
    print("\n--- Security Issues ---")
    issues = await server.get_security_issues("critical")
    print(json.dumps(issues, indent=2))
    
    print("\n--- Immediate Recommendations ---")
    recs = await server.get_recommendations("immediate")
    for rec in recs:
        print(f"  - {rec}")

if __name__ == "__main__":
    asyncio.run(main())