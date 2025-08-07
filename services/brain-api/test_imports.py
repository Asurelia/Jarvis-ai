#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

import sys
import traceback

def test_import(module_name, description=""):
    """Test importing a module and report results"""
    try:
        __import__(module_name)
        print(f"OK {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"FAIL {module_name} - {description}: {e}")
        return False
    except Exception as e:
        print(f"WARN {module_name} - {description}: Unexpected error: {e}")
        return False

def main():
    """Test all required imports"""
    print("Testing Brain API imports...")
    
    # Standard library imports should all work
    standard_libs = [
        ("asyncio", "Async framework"),
        ("json", "JSON handling"),
        ("os", "Operating system interface"),
        ("time", "Time utilities"),
        ("logging", "Logging framework"),
        ("uuid", "UUID generation"),
        ("hashlib", "Hash algorithms"),
        ("typing", "Type hints"),
        ("dataclasses", "Data classes"),
        ("datetime", "Date/time handling"),
        ("collections", "Specialized containers"),
        ("contextlib", "Context managers"),
        ("enum", "Enumerations"),
        ("functools", "Higher-order functions"),
        ("signal", "Signal handling"),
        ("sys", "System interface"),
        ("re", "Regular expressions"),
        ("base64", "Base64 encoding"),
        ("urllib.parse", "URL parsing"),
        ("abc", "Abstract base classes"),
        ("random", "Random number generation"),
        ("math", "Mathematical functions"),
        ("platform", "Platform info"),
        ("subprocess", "Subprocess management")
    ]
    
    print("\nStandard Library Imports:")
    std_results = []
    for module, desc in standard_libs:
        std_results.append(test_import(module, desc))
    
    # External packages that need to be installed
    external_packages = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("pydantic_settings", "Pydantic settings"),
        ("structlog", "Structured logging"),
        ("websockets", "WebSocket support"),
        ("prometheus_client", "Prometheus metrics"),
        ("starlette", "ASGI toolkit"),
        ("numpy", "Numerical computing"),
        ("aiohttp", "HTTP client/server"),
        ("httpx", "HTTP client"),
        ("tenacity", "Retry library"),
        ("psutil", "System utilities"),
        ("aiofiles", "Async file operations")
    ]
    
    print("\nExternal Package Imports:")
    ext_results = []
    for module, desc in external_packages:
        ext_results.append(test_import(module, desc))
    
    # Database packages (likely to fail on Windows without proper setup)
    db_packages = [
        ("asyncpg", "PostgreSQL async driver"),
        ("redis", "Redis client"),
        ("sqlalchemy", "SQL toolkit"),
        ("psycopg2", "PostgreSQL adapter")
    ]
    
    print("\nDatabase Package Imports:")
    db_results = []
    for module, desc in db_packages:
        db_results.append(test_import(module, desc))
    
    # AI/ML packages (heavy dependencies)
    ai_packages = [
        ("sklearn", "Scikit-learn ML"),
        ("sentence_transformers", "Sentence embeddings")
    ]
    
    print("\nAI/ML Package Imports:")
    ai_results = []
    for module, desc in ai_packages:
        ai_results.append(test_import(module, desc))
    
    # Local imports (from the brain-api project)
    local_imports = [
        ("utils.config", "Configuration module"),
        ("utils.security_validators", "Security validators"),
        ("utils.monitoring", "Monitoring utilities")
    ]
    
    print("\nLocal Module Imports:")
    local_results = []
    for module, desc in local_imports:
        local_results.append(test_import(module, desc))
    
    # Summary
    print("\nSummary:")
    print(f"Standard Library: {sum(std_results)}/{len(std_results)} OK")
    print(f"External Packages: {sum(ext_results)}/{len(ext_results)} OK")
    print(f"Database Packages: {sum(db_results)}/{len(db_results)} OK")
    print(f"AI/ML Packages: {sum(ai_results)}/{len(ai_results)} OK")
    print(f"Local Modules: {sum(local_results)}/{len(local_results)} OK")
    
    total_success = sum(std_results + ext_results + db_results + ai_results + local_results)
    total_tests = len(std_results + ext_results + db_results + ai_results + local_results)
    
    print(f"\nOverall: {total_success}/{total_tests} imports successful")
    
    if total_success == total_tests:
        print("All imports are working! Brain API should start successfully.")
        return 0
    else:
        print("Some imports failed. Brain API may have startup issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())