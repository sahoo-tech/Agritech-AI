@echo off
echo 🌱 Starting AgriTech Assistant...
echo 📍 Backend will run on: http://localhost:8000
echo 📍 Frontend will run on: http://localhost:8501
echo ⚠️  Press Ctrl+C to stop both services
echo --------------------------------------------------

REM Start backend server in background
echo 🚀 Starting backend server...
start "AgriTech Backend" python main.py

REM Wait a moment for backend to start
timeout /t 3 /nobreak > nul

REM Start frontend
echo 🌐 Starting frontend...
python -m streamlit run frontend.py --server.port 8501

pause