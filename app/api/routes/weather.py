"""
Weather and Soil Data API routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db, User
from ...core.security import get_current_active_user

router = APIRouter()

# Pydantic models
class LocationRequest(BaseModel):
    latitude: float
    longitude: float

class WeatherResponse(BaseModel):
    current: dict
    forecast_24h: Optional[dict] = None
    agricultural_conditions: dict
    alerts: list
    last_updated: str

class SoilResponse(BaseModel):
    soil_type: str
    ph_level: float
    moisture_content: float
    temperature: Optional[float] = None
    nutrients: dict
    characteristics: dict
    recommendations: list
    last_updated: str

class LocationInfoResponse(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    formatted_address: Optional[str] = None

@router.post("/current", response_model=WeatherResponse)
async def get_current_weather(
    location: LocationRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get current weather conditions for a location (authenticated)"""
    
    try:
        weather_service = request.app.state.weather_service
        
        weather_data = await weather_service.get_weather_data(
            location.latitude, 
            location.longitude
        )
        
        return WeatherResponse(
            current=weather_data.get("current", {}),
            forecast_24h=weather_data.get("forecast_24h", {}),
            agricultural_conditions=weather_data.get("agricultural_conditions", {}),
            alerts=weather_data.get("alerts", []),
            last_updated=weather_data.get("last_updated", "")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")

@router.post("/public/current")
async def get_current_weather_public(
    location: LocationRequest,
    request: Request
):
    """Get current weather conditions for a location (public access)"""
    
    try:
        weather_service = request.app.state.weather_service
        
        weather_data = await weather_service.get_weather_data(
            location.latitude, 
            location.longitude
        )
        
        return {
            "current": weather_data.get("current", {}),
            "forecast_24h": weather_data.get("forecast_24h", {}),
            "agricultural_conditions": weather_data.get("agricultural_conditions", {}),
            "alerts": weather_data.get("alerts", []),
            "last_updated": weather_data.get("last_updated", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")

@router.post("/public/soil")
async def get_soil_data_public(
    location: LocationRequest,
    request: Request
):
    """Get soil analysis for a location (public access)"""
    
    try:
        weather_service = request.app.state.weather_service
        
        soil_data = await weather_service.get_soil_data(
            location.latitude, 
            location.longitude
        )
        
        return soil_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching soil data: {str(e)}")

@router.post("/soil", response_model=SoilResponse)
async def get_soil_data(
    location: LocationRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get soil analysis data for a location"""
    
    try:
        weather_service = request.app.state.weather_service
        
        soil_data = await weather_service.get_soil_data(
            location.latitude,
            location.longitude
        )
        
        return SoilResponse(
            soil_type=soil_data.get("soil_type", "unknown"),
            ph_level=soil_data.get("ph_level", 0.0),
            moisture_content=soil_data.get("moisture_content", 0.0),
            temperature=soil_data.get("temperature"),
            nutrients=soil_data.get("nutrients", {}),
            characteristics=soil_data.get("characteristics", {}),
            recommendations=soil_data.get("recommendations", []),
            last_updated=soil_data.get("last_updated", "")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching soil data: {str(e)}")

@router.post("/location-info", response_model=LocationInfoResponse)
async def get_location_info(
    location: LocationRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get location information from coordinates"""
    
    try:
        weather_service = request.app.state.weather_service
        
        location_info = await weather_service.get_location_info(
            location.latitude,
            location.longitude
        )
        
        if "error" in location_info:
            raise HTTPException(status_code=400, detail=location_info["error"])
        
        return LocationInfoResponse(**location_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting location info: {str(e)}")

@router.post("/comprehensive")
async def get_comprehensive_data(
    location: LocationRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get comprehensive weather, soil, and location data (authenticated)"""
    
    try:
        weather_service = request.app.state.weather_service
        
        # Fetch all data concurrently
        import asyncio
        
        weather_task = weather_service.get_weather_data(location.latitude, location.longitude)
        soil_task = weather_service.get_soil_data(location.latitude, location.longitude)
        location_task = weather_service.get_location_info(location.latitude, location.longitude)
        
        weather_data, soil_data, location_info = await asyncio.gather(
            weather_task, soil_task, location_task
        )
        
        # Combine all data
        comprehensive_data = {
            "location": {
                "coordinates": {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                },
                "info": location_info
            },
            "weather": weather_data,
            "soil": soil_data,
            "farming_recommendations": _generate_farming_recommendations(weather_data, soil_data),
            "timestamp": weather_data.get("last_updated", ""),
            "user_id": current_user.id if current_user else None
        }
        
        return comprehensive_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching comprehensive data: {str(e)}")

@router.post("/public/comprehensive")
async def get_comprehensive_data_public(
    location: LocationRequest,
    request: Request
):
    """Get comprehensive weather, soil, and location data (public access)"""
    
    try:
        weather_service = request.app.state.weather_service
        
        # Fetch all data concurrently
        import asyncio
        
        weather_task = weather_service.get_weather_data(location.latitude, location.longitude)
        soil_task = weather_service.get_soil_data(location.latitude, location.longitude)
        location_task = weather_service.get_location_info(location.latitude, location.longitude)
        
        weather_data, soil_data, location_info = await asyncio.gather(
            weather_task, soil_task, location_task
        )
        
        # Combine all data
        comprehensive_data = {
            "location": {
                "coordinates": {
                    "latitude": location.latitude,
                    "longitude": location.longitude
                },
                "info": location_info
            },
            "weather": weather_data,
            "soil": soil_data,
            "farming_recommendations": _generate_farming_recommendations(weather_data, soil_data),
            "timestamp": weather_data.get("last_updated", ""),
            "data_source": "🔄 Public Access - Login for personalized features"
        }
        
        return comprehensive_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching comprehensive data: {str(e)}")

@router.get("/alerts")
async def get_weather_alerts(
    latitude: float,
    longitude: float,
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get weather alerts for farming activities"""
    
    try:
        weather_service = request.app.state.weather_service
        
        weather_data = await weather_service.get_weather_data(latitude, longitude)
        alerts = weather_data.get("alerts", [])
        
        # Add farming-specific alerts
        farming_alerts = _generate_farming_alerts(weather_data)
        alerts.extend(farming_alerts)
        
        return {
            "alerts": alerts,
            "alert_count": len(alerts),
            "high_priority_count": len([a for a in alerts if a.get("severity") == "high"]),
            "last_updated": weather_data.get("last_updated", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

@router.get("/forecast")
async def get_weather_forecast(
    latitude: float,
    longitude: float,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    days: int = 5
):
    """Get extended weather forecast"""
    
    try:
        weather_service = request.app.state.weather_service
        
        # For now, return current weather data
        # In a real implementation, this would fetch extended forecast
        weather_data = await weather_service.get_weather_data(latitude, longitude)
        
        # Mock extended forecast based on current conditions
        forecast = _generate_mock_forecast(weather_data, days)
        
        return {
            "forecast": forecast,
            "days": days,
            "location": {"latitude": latitude, "longitude": longitude},
            "last_updated": weather_data.get("last_updated", "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forecast: {str(e)}")

@router.post("/irrigation-advice")
async def get_irrigation_advice(
    location: LocationRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    crop_type: Optional[str] = None
):
    """Get irrigation recommendations based on weather and soil conditions"""
    
    try:
        weather_service = request.app.state.weather_service
        
        weather_data = await weather_service.get_weather_data(location.latitude, location.longitude)
        soil_data = await weather_service.get_soil_data(location.latitude, location.longitude)
        
        irrigation_advice = _generate_irrigation_advice(weather_data, soil_data, crop_type)
        
        return irrigation_advice
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating irrigation advice: {str(e)}")

def _generate_farming_recommendations(weather_data: dict, soil_data: dict) -> dict:
    """Generate farming recommendations based on weather and soil data"""
    
    recommendations = {
        "immediate_actions": [],
        "this_week": [],
        "general_advice": []
    }
    
    # Weather-based recommendations
    current_weather = weather_data.get("current", {})
    temp = current_weather.get("temperature", 20)
    humidity = current_weather.get("humidity", 50)
    
    if temp > 30:
        recommendations["immediate_actions"].append("Increase irrigation frequency due to high temperature")
    
    if humidity > 80:
        recommendations["immediate_actions"].append("Monitor crops for fungal diseases due to high humidity")
    
    # Soil-based recommendations
    soil_moisture = soil_data.get("moisture_content", 50)
    ph_level = soil_data.get("ph_level", 7.0)
    
    if soil_moisture < 30:
        recommendations["immediate_actions"].append("Soil moisture is low - consider irrigation")
    
    if ph_level < 6.0:
        recommendations["this_week"].append("Consider adding lime to raise soil pH")
    elif ph_level > 7.5:
        recommendations["this_week"].append("Consider adding sulfur to lower soil pH")
    
    # General advice
    recommendations["general_advice"] = [
        "Monitor weather conditions daily",
        "Check soil moisture regularly",
        "Inspect crops for signs of disease or pests",
        "Maintain proper nutrition schedule"
    ]
    
    return recommendations

def _generate_farming_alerts(weather_data: dict) -> list:
    """Generate farming-specific alerts"""
    
    alerts = []
    current = weather_data.get("current", {})
    
    # Check for optimal spraying conditions
    wind_speed = current.get("wind_speed", 0)
    if wind_speed > 15:
        alerts.append({
            "type": "spraying_warning",
            "message": "Wind speed too high for pesticide/herbicide application",
            "severity": "medium"
        })
    
    # Check for planting conditions
    temp = current.get("temperature", 20)
    if temp < 10:
        alerts.append({
            "type": "planting_warning",
            "message": "Temperature too low for most crop planting",
            "severity": "medium"
        })
    
    return alerts

def _generate_mock_forecast(weather_data: dict, days: int) -> list:
    """Generate mock forecast data"""
    
    import random
    from datetime import datetime, timedelta
    
    current = weather_data.get("current", {})
    base_temp = current.get("temperature", 20)
    
    forecast = []
    for i in range(days):
        date = datetime.now() + timedelta(days=i)
        temp_variation = random.uniform(-5, 5)
        
        forecast.append({
            "date": date.strftime("%Y-%m-%d"),
            "temperature": {
                "min": round(base_temp + temp_variation - 3, 1),
                "max": round(base_temp + temp_variation + 3, 1)
            },
            "humidity": random.randint(40, 80),
            "precipitation_chance": random.randint(0, 100),
            "wind_speed": random.uniform(5, 20),
            "description": random.choice(["Sunny", "Partly cloudy", "Cloudy", "Light rain"])
        })
    
    return forecast

def _generate_irrigation_advice(weather_data: dict, soil_data: dict, crop_type: str = None) -> dict:
    """Generate irrigation advice"""
    
    current = weather_data.get("current", {})
    temp = current.get("temperature", 20)
    humidity = current.get("humidity", 50)
    
    soil_moisture = soil_data.get("moisture_content", 50)
    
    advice = {
        "irrigation_needed": False,
        "urgency": "low",
        "recommended_amount": "0mm",
        "timing": "morning",
        "reasoning": [],
        "next_check": "24 hours"
    }
    
    # Determine irrigation need
    if soil_moisture < 30:
        advice["irrigation_needed"] = True
        advice["urgency"] = "high"
        advice["recommended_amount"] = "25-30mm"
        advice["reasoning"].append("Soil moisture is critically low")
    elif soil_moisture < 50 and temp > 25:
        advice["irrigation_needed"] = True
        advice["urgency"] = "medium"
        advice["recommended_amount"] = "15-20mm"
        advice["reasoning"].append("Moderate soil moisture with high temperature")
    
    # Adjust for crop type
    if crop_type:
        if crop_type.lower() in ["tomato", "cucumber", "lettuce"]:
            advice["reasoning"].append(f"{crop_type} requires consistent moisture")
        elif crop_type.lower() in ["wheat", "corn"]:
            advice["reasoning"].append(f"{crop_type} is more drought tolerant")
    
    # Weather considerations
    if humidity > 80:
        advice["timing"] = "early morning"
        advice["reasoning"].append("High humidity - irrigate early to reduce disease risk")
    
    return advice