#!/usr/bin/env python3
"""
FlightVault API Server Launcher
"""

if __name__ == "__main__":
    from src.api.main import app
    import uvicorn
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")