#!/usr/bin/env python3
"""
Simple script to run the FastAPI application
Can be executed directly from IDE or command line
"""

import uvicorn
import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting LeadFlow Scraper Service...")
    print("📍 API will be available at: http://localhost:3002")
    print("📚 API Documentation: http://localhost:3002/docs")
    print("🔧 Debug mode: ENABLED")
    print("🔄 Auto-reload: ENABLED")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=3002,
        reload=True,
        log_level="debug",
        access_log=True
    )


