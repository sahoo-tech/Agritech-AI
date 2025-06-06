# 🚀 Quick Start Guide - Agritech AI

## ⚡ Fastest Way to Get Started

### Option 1: Frontend Only (Immediate Demo)
```bash
# Install dependencies
pip install streamlit requests plotly folium streamlit-folium pillow

# Run the demo (works without API server)
streamlit run demo_frontend.py
```
**✅ This will work immediately with simulated data!**

### Option 2: Full Application
```bash
# 1. Install all dependencies
pip install -r requirements.txt

# 2. Copy environment file
cp .env.example .env

# 3. Start API server (Terminal 1)
python run.py

# 4. Start frontend (Terminal 2) 
streamlit run frontend.py
```

## 🔧 Troubleshooting "Soil Data Not Available"

### Problem: Soil data shows as unavailable
**Cause:** The frontend is trying to connect to the API server, but it's not running.

### Solutions:

#### Quick Fix (Use Simulated Data):
- The updated frontend now automatically falls back to simulated data
- You'll see: "🔄 API server not running, using simulated soil data"
- This is normal and expected when running frontend-only

#### Full Fix (Real API Data):
1. **Start the API server first:**
   ```bash
   python run.py
   ```
   Wait for: "🌱 Starting AgriTech Assistant Development Server..."

2. **Then start the frontend:**
   ```bash
   streamlit run frontend.py
   ```

3. **Verify API is running:**
   - Open: http://localhost:8000/docs
   - You should see the API documentation

## 📱 Access Points

- **Demo Frontend:** http://localhost:8501 (after `streamlit run demo_frontend.py`)
- **Full Frontend:** http://localhost:8501 (after `streamlit run frontend.py`) 
- **API Server:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

## 🎯 What Each Mode Provides

### Demo Mode (`demo_frontend.py`)
- ✅ Works immediately without setup
- ✅ Simulated soil and weather data
- ✅ All UI features functional
- ✅ Perfect for demonstrations

### Full Mode (`frontend.py` + API)
- ✅ Real-time weather data (with API keys)
- ✅ Database storage
- ✅ User authentication
- ✅ ML disease detection
- ✅ Complete feature set

## 🔑 API Keys (Optional)

Add to `.env` file for real data:
```env
OPENAI_API_KEY=your-openai-key
WEATHER_API_KEY=your-openweathermap-key
SOIL_API_KEY=your-soil-api-key
```

**Note:** The application works perfectly without API keys using simulated data!

## 🆘 Still Having Issues?

1. **Check Python version:** `python --version` (needs 3.8+)
2. **Install missing packages:** `pip install -r requirements.txt`
3. **Try demo mode first:** `streamlit run demo_frontend.py`
4. **Check if ports are free:** 8000 (API) and 8501 (Frontend)

## 🎉 Success Indicators

- ✅ **Demo working:** You see the Agritech interface with simulated data
- ✅ **API working:** You see "🌱 Starting AgriTech Assistant..." message
- ✅ **Full app working:** Real-time data loads without "🔄 simulated data" messages