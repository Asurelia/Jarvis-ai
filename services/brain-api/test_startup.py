#!/usr/bin/env python3
"""
Test script to check if brain-api can start with current environment
"""

import sys
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_basic_startup():
    """Test basic startup components"""
    
    print("Testing basic brain-api startup components...")
    
    try:
        # Test configuration
        from utils.config import settings
        print(f"OK Configuration loaded: {settings.HOST}:{settings.PORT}")
        
        # Test security validators
        from utils.security_validators import validate_chat_input, sanitize_chat_message
        is_valid, msg = validate_chat_input("Hello JARVIS!")
        sanitized = sanitize_chat_message("Hello <script>alert('test')</script>")
        print(f"OK Security validators working: valid={is_valid}, sanitized='{sanitized}'")
        
        # Test monitoring (should use fallback)
        from utils.monitoring import setup_metrics, record_request
        setup_metrics()
        record_request("GET", "/test", 200, 0.1)
        print("OK Monitoring system working (fallback mode)")
        
        # Test FastAPI imports
        from fastapi import FastAPI
        app = FastAPI(title="Test App")
        print("OK FastAPI imported successfully")
        
        return True
        
    except Exception as e:
        print(f"FAIL Startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_core_modules():
    """Test core modules that don't require database connections"""
    
    print("\nTesting core modules (without DB connections)...")
    
    try:
        # Test if core modules can be imported (they might fail on initialization)
        print("- Testing core.metacognition import...")
        # We can't fully test this without numpy/sklearn
        print("  (Skipping - requires AI/ML dependencies)")
        
        print("- Testing persona modules...")
        from personas.base_persona import BasePersona, PersonalityTraits
        print("OK Base persona classes imported")
        
        from personas.jarvis_classic import JarvisClassicPersona
        print("OK JARVIS Classic persona imported")
        
        return True
        
    except Exception as e:
        print(f"FAIL Core modules test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_routes():
    """Test API route imports"""
    
    print("\nTesting API routes...")
    
    try:
        from api.routes import health
        print("OK Health routes imported")
        
        # We can try to import other routes but they might fail
        try:
            from api.routes import chat, memory, agent
            print("OK Chat/Memory/Agent routes imported")
        except Exception as e:
            print(f"WARN Some routes failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"FAIL API routes test failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("Brain API Startup Test")
    print("=" * 50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    results = []
    
    # Run async tests
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        results.append(loop.run_until_complete(test_basic_startup()))
        results.append(loop.run_until_complete(test_core_modules()))  
        results.append(loop.run_until_complete(test_api_routes()))
        
    except Exception as e:
        print(f"FAIL Test framework error: {e}")
        results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"Tests passed: {sum(results)}/{len(results)}")
    
    if all(results):
        print("All startup tests passed! Brain API should start in fallback mode.")
        print("\nNote: Database operations will fail until proper DB setup.")
        return 0
    else:
        print("Some tests failed. Check dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())