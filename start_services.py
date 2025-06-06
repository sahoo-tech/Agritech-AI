#!/usr/bin/env python3
"""
AgriTech Assistant - Service Starter
Starts both backend and frontend services
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def start_backend():
    """Start the FastAPI backend server"""
    print("🚀 Starting AgriTech Backend API...")
    backend_process = subprocess.Popen([
        sys.executable, "main.py"
    ], cwd=Path(__file__).parent)
    return backend_process

def start_frontend():
    """Start the Streamlit frontend"""
    print("🌐 Starting AgriTech Frontend Dashboard...")
    frontend_process = subprocess.Popen([
        sys.executable, "-m", "streamlit", "run", "frontend.py", 
        "--server.port", "8501",
        "--server.headless", "true"
    ], cwd=Path(__file__).parent)
    return frontend_process

def main():
    """Main function to start both services"""
    print("🌱 AgriTech Assistant - Starting Services...")
    print("=" * 50)
    
    # Start backend
    backend_proc = start_backend()
    
    # Wait a bit for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(5)
    
    # Start frontend
    frontend_proc = start_frontend()
    
    print("\n✅ Services Started Successfully!")
    print("=" * 50)
    print("🌐 Main Landing Page: http://localhost:8000")
    print("📊 Dashboard: http://localhost:8501")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("=" * 50)
    print("\n💡 Tips:")
    print("- Use the dashboard for interactive features")
    print("- Check the API docs for integration")
    print("- Both services support guest access")
    print("\n🛑 Press Ctrl+C to stop all services")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("✅ All services stopped.")

if __name__ == "__main__":
    main()