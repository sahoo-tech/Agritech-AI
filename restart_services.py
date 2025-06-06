#!/usr/bin/env python3
"""
AgriTech Assistant - Service Restarter
Stops existing services and starts fresh ones
"""

import subprocess
import time
import sys
import os
from pathlib import Path

def kill_existing_services():
    """Kill existing Python processes"""
    try:
        # Kill all Python processes (be careful with this in production)
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                      capture_output=True, check=False)
        print("🛑 Stopped existing services")
        time.sleep(2)
    except Exception as e:
        print(f"Note: {e}")

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
    """Main function to restart both services"""
    print("🔄 AgriTech Assistant - Restarting Services...")
    print("=" * 50)
    
    # Kill existing services
    kill_existing_services()
    
    # Start backend
    backend_proc = start_backend()
    
    # Wait for backend to start
    print("⏳ Waiting for backend to initialize...")
    time.sleep(5)
    
    # Start frontend
    frontend_proc = start_frontend()
    
    print("\n✅ Services Restarted Successfully!")
    print("=" * 50)
    print("🌐 Main Landing Page: http://localhost:8000")
    print("📊 Dashboard: http://localhost:8501")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("=" * 50)
    print("\n🆕 New Features Available:")
    print("• 📷 Camera capture for disease detection")
    print("• 🔄 Enhanced mock data with realistic patterns")
    print("• 🌤️ Improved weather and soil analysis")
    print("• 📱 Better mobile-responsive design")
    print("• 🎯 Detailed disease analysis results")
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