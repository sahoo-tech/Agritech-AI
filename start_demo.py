#!/usr/bin/env python3
"""
AgriTech Assistant - Demo Startup Script
Starts both backend API and frontend demo
"""

import subprocess
import time
import sys
import os
import threading
import webbrowser
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting AgriTech Backend API...")
    try:
        # Start the backend server
        subprocess.run([
            sys.executable, "run.py"
        ], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Backend server stopped")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

def start_frontend():
    """Start the Streamlit frontend"""
    print("🌐 Starting AgriTech Frontend...")
    time.sleep(3)  # Wait for backend to start
    
    try:
        # Start the frontend
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "demo_frontend.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ], cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n🛑 Frontend server stopped")
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")

def check_backend_health():
    """Check if backend is running"""
    import requests
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main startup function"""
    print("🌱 AgriTech Assistant - Demo Startup")
    print("=" * 50)
    
    # Check if backend is already running
    if check_backend_health():
        print("✅ Backend is already running at http://localhost:8000")
        start_frontend()
        return
    
    print("🔧 Starting both backend and frontend servers...")
    print("📍 Backend API: http://localhost:8000")
    print("📍 Frontend Demo: http://localhost:8501")
    print("📚 API Docs: http://localhost:8000/docs")
    print("\n⏳ Please wait while servers start up...")
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend, daemon=True)
    backend_thread.start()
    
    # Wait for backend to be ready
    print("⏳ Waiting for backend to start...")
    for i in range(30):  # Wait up to 30 seconds
        if check_backend_health():
            print("✅ Backend is ready!")
            break
        time.sleep(1)
        print(f"⏳ Waiting... ({i+1}/30)")
    else:
        print("❌ Backend failed to start within 30 seconds")
        return
    
    # Open browser tabs
    print("🌐 Opening browser tabs...")
    try:
        webbrowser.open("http://localhost:8501")  # Frontend
        time.sleep(1)
        webbrowser.open("http://localhost:8000/docs")  # API docs
    except:
        print("⚠️ Could not open browser automatically")
    
    # Start frontend (this will block)
    start_frontend()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down AgriTech Assistant...")
        print("👋 Thank you for using AgriTech Assistant!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)