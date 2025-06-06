# Quick Start Guide - Fixing "Connection Refused" Error

## Problem
The Quick Stats section shows "target machine actively refusing connection" error because the backend server is not running.

## Solution

### Option 1: Use the Automated Starter (Recommended)
1. **Windows Users**: Double-click `start_app.bat`
2. **All Users**: Run `python start_app.py`

This will automatically start both the backend and frontend servers.

### Option 2: Manual Start
1. **Start Backend Server** (in one terminal):
   ```bash
   python main.py
   ```
   Wait for "Application startup complete" message.

2. **Start Frontend** (in another terminal):
   ```bash
   streamlit run frontend.py --server.port 8501
   ```

### Option 3: Use Offline Mode
If you don't want to start the backend server, the Quick Stats will now automatically show demo data with a helpful message.

## What's Fixed
- ✅ Added connection error handling
- ✅ Fallback to realistic demo data when backend is offline
- ✅ Clear user messages about data source
- ✅ No more error messages in Quick Stats
- ✅ Graceful degradation when server is unavailable

## URLs
- **Backend API**: http://localhost:8000
- **Frontend**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs

## Notes
- The Quick Stats will show "🔄 Offline Demo Data" when backend is not running
- Start the backend server for real weather data from OpenWeatherMap API
- Demo data is location-aware and changes based on coordinates and time