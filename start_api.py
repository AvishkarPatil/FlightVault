"""
FlightVault API Server Launcher
"""

import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting FlightVault API Server...")
    print("📡 API Documentation: http://localhost:8000/docs")
    print("🔄 Interactive API: http://localhost:8000/redoc")
    print("❤️  Health Check: http://localhost:8000/health")
    print()
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )