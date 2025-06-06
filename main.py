"""
AgriTech Assistant - Python FastAPI Backend
A comprehensive agricultural assistance application with AI-powered features
"""

import os
import uvicorn
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# Import our modules
from app.core.config import settings
from app.api.routes import disease_detection, chatbot, weather, auth, crop_yield, iot_sensors, marketplace, community, offline
from app.core.database import engine, Base
from app.ml.disease_detector import DiseaseDetector
from app.services.weather_service import WeatherService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
disease_detector = None
weather_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global disease_detector, weather_service
    
    # Startup
    logger.info("Starting AgriTech Assistant...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize ML models
    disease_detector = DiseaseDetector()
    await disease_detector.load_model()
    
    # Initialize services
    weather_service = WeatherService()
    
    # Store in app state
    app.state.disease_detector = disease_detector
    app.state.weather_service = weather_service
    
    logger.info("AgriTech Assistant started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AgriTech Assistant...")

# Create FastAPI app
app = FastAPI(
    title="AgriTech Assistant API",
    description="AI-powered agricultural assistance platform",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(disease_detection.router, prefix="/api/disease", tags=["Disease Detection"])
app.include_router(chatbot.router, prefix="/api/chat", tags=["AI Assistant"])
app.include_router(weather.router, prefix="/api/weather", tags=["Weather & Soil"])

# New roadmap features
app.include_router(crop_yield.router, prefix="/api", tags=["Crop Yield Prediction"])
app.include_router(iot_sensors.router, prefix="/api", tags=["IoT Sensors"])
app.include_router(marketplace.router, prefix="/api", tags=["Marketplace"])
app.include_router(community.router, prefix="/api", tags=["Community Forum"])
app.include_router(offline.router, prefix="/api", tags=["Offline Services"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "database": "connected",
            "ml_models": "loaded",
            "weather_service": "active"
        }
    }

# Serve static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve the frontend
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main application page"""
    try:
        with open("templates/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>AgriTech Assistant</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #2c3e50; text-align: center; }
                .feature { background: #ecf0f1; padding: 20px; margin: 15px 0; border-radius: 8px; }
                .api-link { display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
                .api-link:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🌱 AgriTech Assistant API</h1>
                <p>Welcome to the AgriTech Assistant - your AI-powered agricultural companion!</p>
                
                <div class="feature">
                    <h3>🔍 Disease Detection</h3>
                    <p>Upload plant images to detect diseases using advanced computer vision</p>
                </div>
                
                <div class="feature">
                    <h3>💬 AI Assistant</h3>
                    <p>Chat with our multilingual AI for personalized farming advice</p>
                </div>
                
                <div class="feature">
                    <h3>🌤️ Weather & Soil Data</h3>
                    <p>Get hyperlocal weather conditions and soil analysis</p>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/docs" class="api-link">📚 API Documentation</a>
                    <a href="/redoc" class="api-link">📖 ReDoc</a>
                </div>
            </div>
        </body>
        </html>
        """)



if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )