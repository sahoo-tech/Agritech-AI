#!/usr/bin/env python3
"""
AgriTech Assistant - Application Starter
Starts both backend and frontend services
"""

import subprocess
import sys
import time
import threading
import os

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting backend server...")
    try:
        subprocess.run([sys.executable, "main.py"], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("🛑 Backend server stopped")

def start_frontend():
    """Start the Streamlit frontend"""
    print("🌐 Starting frontend...")
    time.sleep(3)  # Give backend time to start
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "frontend.py", 
            "--server.port", "8501"
        ], cwd=os.getcwd())
    except KeyboardInterrupt:
        print("🛑 Frontend stopped")

def main():
    """Start both services"""
    print("🌱 Starting AgriTech Assistant...")
    print("📍 Backend will run on: http://localhost:8000")
    print("📍 Frontend will run on: http://localhost:8501")
    print("⚠️  Press Ctrl+C to stop both services")
    print("-" * 50)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Start frontend in main thread
    try:
        start_frontend()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down AgriTech Assistant...")
        sys.exit(0)

if __name__ == "__main__":
    main()