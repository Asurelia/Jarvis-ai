#!/usr/bin/env python3
"""
Test the health endpoint functionality
"""

import asyncio
import logging
from fastapi.testclient import TestClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_app():
    """Create a minimal test app with health endpoint"""
    
    from fastapi import FastAPI
    from api.routes import health
    
    app = FastAPI(title="JARVIS Brain API Test")
    app.include_router(health.router, prefix="/health", tags=["Health"])
    
    return app

def test_health_endpoint():
    """Test the health endpoint"""
    
    print("Testing Health Endpoint...")
    
    try:
        # Create test app
        app = create_test_app()
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        
        print(f"Health endpoint status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Health endpoint response:")
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"  {key}:")
                    for k, v in value.items():
                        print(f"    {k}: {v}")
                else:
                    print(f"  {key}: {value}")
            
            return True
        else:
            print(f"Health endpoint failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"Health endpoint test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print("Brain API Health Endpoint Test")
    print("=" * 50)
    
    success = test_health_endpoint()
    
    print("\n" + "=" * 50)
    if success:
        print("Health endpoint test PASSED")
        print("The health endpoint should work when the service starts.")
        return 0
    else:
        print("Health endpoint test FAILED")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())