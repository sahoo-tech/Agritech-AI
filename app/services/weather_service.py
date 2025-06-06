"""
Weather and Soil Data Service
Provides hyperlocal weather conditions and soil analysis
"""

import asyncio
import aiohttp
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from sqlalchemy.orm import Session
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

from ..core.config import settings
from ..core.database import WeatherData, SoilData, SessionLocal

logger = logging.getLogger(__name__)

class WeatherService:
    """Enhanced weather and soil data service"""
    
    def __init__(self):
        self.session = None
        self.geocoder = Nominatim(user_agent="agritech-assistant")
        self.cache_duration = timedelta(minutes=settings.WEATHER_CACHE_DURATION)
        
        # Soil type mapping based on location characteristics
        self.soil_types = {
            "clay": {"ph": 6.5, "drainage": "poor", "nutrients": "high"},
            "sandy": {"ph": 6.0, "drainage": "excellent", "nutrients": "low"},
            "loam": {"ph": 6.8, "drainage": "good", "nutrients": "medium"},
            "silt": {"ph": 7.0, "drainage": "moderate", "nutrients": "medium"},
            "peat": {"ph": 5.5, "drainage": "poor", "nutrients": "very_high"},
            "chalk": {"ph": 8.0, "drainage": "good", "nutrients": "low"}
        }
    
    async def get_weather_data(self, latitude: float, longitude: float) -> Dict:
        """Get comprehensive weather data for location"""
        try:
            # Check cache first
            cached_data = await self._get_cached_weather(latitude, longitude)
            if cached_data:
                return cached_data
            
            # Fetch fresh data
            weather_data = await self._fetch_weather_data(latitude, longitude)
            
            # Cache the data
            await self._cache_weather_data(latitude, longitude, weather_data)
            
            return weather_data
            
        except Exception as e:
            logger.error(f"Error getting weather data: {e}")
            return await self._get_fallback_weather_data(latitude, longitude)
    
    async def get_soil_data(self, latitude: float, longitude: float) -> Dict:
        """Get soil analysis data for location"""
        try:
            # Check cache first
            cached_data = await self._get_cached_soil_data(latitude, longitude)
            if cached_data:
                return cached_data
            
            # Generate soil data based on location and weather
            soil_data = await self._generate_soil_data(latitude, longitude)
            
            # Cache the data
            await self._cache_soil_data(latitude, longitude, soil_data)
            
            return soil_data
            
        except Exception as e:
            logger.error(f"Error getting soil data: {e}")
            return await self._get_fallback_soil_data()
    
    async def get_location_info(self, latitude: float, longitude: float) -> Dict:
        """Get location information from coordinates"""
        try:
            location = await asyncio.get_event_loop().run_in_executor(
                None, self.geocoder.reverse, f"{latitude}, {longitude}"
            )
            
            if location:
                address = location.raw.get('address', {})
                return {
                    "address": location.address,
                    "city": address.get('city', address.get('town', address.get('village', ''))),
                    "state": address.get('state', ''),
                    "country": address.get('country', ''),
                    "postcode": address.get('postcode', ''),
                    "formatted_address": location.address
                }
            else:
                return {"error": "Location not found"}
                
        except GeocoderTimedOut:
            return {"error": "Geocoding service timeout"}
        except Exception as e:
            logger.error(f"Error getting location info: {e}")
            return {"error": str(e)}
    
    async def _fetch_weather_data(self, latitude: float, longitude: float) -> Dict:
        """Fetch weather data from external API"""
        if not settings.WEATHER_API_KEY:
            return await self._generate_mock_weather_data(latitude, longitude)
        
        try:
            async with aiohttp.ClientSession() as session:
                # Current weather
                current_url = f"{settings.WEATHER_API_BASE_URL}/weather"
                current_params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": settings.WEATHER_API_KEY,
                    "units": "metric"
                }
                
                async with session.get(current_url, params=current_params) as response:
                    if response.status == 200:
                        current_data = await response.json()
                    else:
                        raise Exception(f"Weather API error: {response.status}")
                
                # Forecast data
                forecast_url = f"{settings.WEATHER_API_BASE_URL}/forecast"
                forecast_params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": settings.WEATHER_API_KEY,
                    "units": "metric",
                    "cnt": 8  # 24 hours (3-hour intervals)
                }
                
                async with session.get(forecast_url, params=forecast_params) as response:
                    if response.status == 200:
                        forecast_data = await response.json()
                    else:
                        forecast_data = {"list": []}
                
                return await self._process_weather_data(current_data, forecast_data)
                
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return await self._generate_mock_weather_data(latitude, longitude)
    
    async def _process_weather_data(self, current: Dict, forecast: Dict) -> Dict:
        """Process raw weather data into structured format"""
        try:
            main = current.get("main", {})
            weather = current.get("weather", [{}])[0]
            wind = current.get("wind", {})
            sys = current.get("sys", {})
            
            # Process forecast for trends
            forecast_list = forecast.get("list", [])
            hourly_temps = [item["main"]["temp"] for item in forecast_list[:8]]
            hourly_humidity = [item["main"]["humidity"] for item in forecast_list[:8]]
            
            processed_data = {
                "current": {
                    "temperature": main.get("temp", 0),
                    "feels_like": main.get("feels_like", 0),
                    "humidity": main.get("humidity", 0),
                    "pressure": main.get("pressure", 0),
                    "visibility": current.get("visibility", 0) / 1000,  # Convert to km
                    "uv_index": 0,  # Would need separate UV API call
                    "description": weather.get("description", ""),
                    "icon": weather.get("icon", ""),
                    "wind_speed": wind.get("speed", 0) * 3.6,  # Convert m/s to km/h
                    "wind_direction": wind.get("deg", 0),
                    "sunrise": datetime.fromtimestamp(sys.get("sunrise", 0)),
                    "sunset": datetime.fromtimestamp(sys.get("sunset", 0))
                },
                "forecast_24h": {
                    "temperature_trend": self._calculate_trend(hourly_temps),
                    "humidity_trend": self._calculate_trend(hourly_humidity),
                    "min_temp": min(hourly_temps) if hourly_temps else 0,
                    "max_temp": max(hourly_temps) if hourly_temps else 0,
                    "avg_humidity": sum(hourly_humidity) / len(hourly_humidity) if hourly_humidity else 0
                },
                "agricultural_conditions": self._assess_agricultural_conditions(main, weather, wind),
                "alerts": self._generate_weather_alerts(main, weather, wind),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing weather data: {e}")
            return await self._generate_mock_weather_data(0, 0)
    
    def _calculate_trend(self, values: list) -> str:
        """Calculate trend from a list of values"""
        if len(values) < 2:
            return "stable"
        
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        if diff > 2:
            return "increasing"
        elif diff < -2:
            return "decreasing"
        else:
            return "stable"
    
    def _assess_agricultural_conditions(self, main: Dict, weather: Dict, wind: Dict) -> Dict:
        """Assess conditions for agricultural activities"""
        temp = main.get("temp", 20)
        humidity = main.get("humidity", 50)
        wind_speed = wind.get("speed", 0) * 3.6
        weather_main = weather.get("main", "").lower()
        
        conditions = {
            "irrigation_needed": False,
            "pest_risk": "low",
            "disease_risk": "low",
            "planting_conditions": "good",
            "harvesting_conditions": "good",
            "spraying_conditions": "good"
        }
        
        # Irrigation assessment
        if humidity < 40 and temp > 25:
            conditions["irrigation_needed"] = True
        
        # Pest risk assessment
        if 20 <= temp <= 30 and humidity > 60:
            conditions["pest_risk"] = "high"
        elif 15 <= temp <= 35 and 40 <= humidity <= 80:
            conditions["pest_risk"] = "moderate"
        
        # Disease risk assessment
        if humidity > 80 and temp > 15:
            conditions["disease_risk"] = "high"
        elif humidity > 60 and temp > 10:
            conditions["disease_risk"] = "moderate"
        
        # Weather-based conditions
        if "rain" in weather_main or wind_speed > 20:
            conditions["spraying_conditions"] = "poor"
            conditions["harvesting_conditions"] = "poor"
        
        if temp < 5 or temp > 35:
            conditions["planting_conditions"] = "poor"
        
        return conditions
    
    def _generate_weather_alerts(self, main: Dict, weather: Dict, wind: Dict) -> list:
        """Generate weather-based alerts for farmers"""
        alerts = []
        
        temp = main.get("temp", 20)
        humidity = main.get("humidity", 50)
        wind_speed = wind.get("speed", 0) * 3.6
        weather_main = weather.get("main", "").lower()
        
        if temp > 35:
            alerts.append({
                "type": "heat_warning",
                "message": "High temperature alert: Ensure adequate irrigation and shade for crops",
                "severity": "high"
            })
        
        if temp < 0:
            alerts.append({
                "type": "frost_warning",
                "message": "Frost warning: Protect sensitive crops from freezing temperatures",
                "severity": "high"
            })
        
        if humidity > 85:
            alerts.append({
                "type": "disease_risk",
                "message": "High humidity increases disease risk: Monitor crops closely",
                "severity": "medium"
            })
        
        if wind_speed > 25:
            alerts.append({
                "type": "wind_warning",
                "message": "Strong winds: Avoid spraying and secure loose structures",
                "severity": "medium"
            })
        
        if "storm" in weather_main or "thunder" in weather_main:
            alerts.append({
                "type": "storm_warning",
                "message": "Storm warning: Secure equipment and avoid outdoor activities",
                "severity": "high"
            })
        
        return alerts
    
    async def _generate_soil_data(self, latitude: float, longitude: float) -> Dict:
        """Generate soil data based on location and environmental factors"""
        try:
            # Get weather data to inform soil conditions
            weather_data = await self.get_weather_data(latitude, longitude)
            
            # Determine soil type based on location (simplified)
            soil_type = self._determine_soil_type(latitude, longitude)
            soil_characteristics = self.soil_types.get(soil_type, self.soil_types["loam"])
            
            # Generate realistic soil data
            base_ph = soil_characteristics["ph"]
            current_temp = weather_data.get("current", {}).get("temperature", 20)
            current_humidity = weather_data.get("current", {}).get("humidity", 50)
            
            # Adjust values based on weather
            moisture_content = min(100, max(10, current_humidity * 0.8 + (current_temp - 20) * -2))
            ph_level = base_ph + (current_temp - 20) * 0.01  # Slight pH variation with temperature
            
            soil_data = {
                "soil_type": soil_type,
                "ph_level": round(ph_level, 1),
                "moisture_content": round(moisture_content, 1),
                "temperature": round(current_temp - 2, 1),  # Soil temp slightly lower
                "nutrients": {
                    "nitrogen": self._generate_nutrient_level("nitrogen", soil_type),
                    "phosphorus": self._generate_nutrient_level("phosphorus", soil_type),
                    "potassium": self._generate_nutrient_level("potassium", soil_type),
                    "organic_matter": self._generate_nutrient_level("organic_matter", soil_type)
                },
                "characteristics": {
                    "drainage": soil_characteristics["drainage"],
                    "nutrient_retention": soil_characteristics["nutrients"],
                    "compaction_risk": self._assess_compaction_risk(soil_type, moisture_content),
                    "erosion_risk": self._assess_erosion_risk(soil_type, weather_data)
                },
                "recommendations": self._generate_soil_recommendations(soil_type, ph_level, moisture_content),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            return soil_data
            
        except Exception as e:
            logger.error(f"Error generating soil data: {e}")
            return await self._get_fallback_soil_data()
    
    def _determine_soil_type(self, latitude: float, longitude: float) -> str:
        """Determine soil type based on geographic location"""
        # Simplified soil type determination based on latitude
        # In a real application, this would use soil survey data
        
        abs_lat = abs(latitude)
        
        if abs_lat > 60:  # Arctic regions
            return "peat"
        elif abs_lat > 45:  # Temperate regions
            return "loam"
        elif abs_lat > 30:  # Subtropical regions
            return "clay"
        elif abs_lat > 15:  # Tropical regions
            return "sandy"
        else:  # Equatorial regions
            return "silt"
    
    def _generate_nutrient_level(self, nutrient: str, soil_type: str) -> Dict:
        """Generate nutrient level data"""
        import random
        
        # Base levels by soil type
        base_levels = {
            "clay": {"nitrogen": 45, "phosphorus": 35, "potassium": 40, "organic_matter": 3.5},
            "sandy": {"nitrogen": 20, "phosphorus": 15, "potassium": 25, "organic_matter": 1.5},
            "loam": {"nitrogen": 35, "phosphorus": 25, "potassium": 30, "organic_matter": 2.8},
            "silt": {"nitrogen": 30, "phosphorus": 20, "potassium": 28, "organic_matter": 2.2},
            "peat": {"nitrogen": 60, "phosphorus": 45, "potassium": 35, "organic_matter": 8.0},
            "chalk": {"nitrogen": 25, "phosphorus": 18, "potassium": 22, "organic_matter": 1.8}
        }
        
        base_value = base_levels.get(soil_type, base_levels["loam"])[nutrient]
        
        # Add some variation
        variation = random.uniform(-0.2, 0.2) * base_value
        final_value = max(0, base_value + variation)
        
        # Determine status
        if nutrient == "organic_matter":
            if final_value > 4:
                status = "high"
            elif final_value > 2:
                status = "adequate"
            else:
                status = "low"
            unit = "%"
        else:
            if final_value > 40:
                status = "high"
            elif final_value > 20:
                status = "adequate"
            else:
                status = "low"
            unit = "mg/kg"
        
        return {
            "value": round(final_value, 1),
            "unit": unit,
            "status": status
        }
    
    def _assess_compaction_risk(self, soil_type: str, moisture_content: float) -> str:
        """Assess soil compaction risk"""
        if soil_type == "clay" and moisture_content > 70:
            return "high"
        elif soil_type in ["silt", "loam"] and moisture_content > 80:
            return "moderate"
        else:
            return "low"
    
    def _assess_erosion_risk(self, soil_type: str, weather_data: Dict) -> str:
        """Assess soil erosion risk"""
        wind_speed = weather_data.get("current", {}).get("wind_speed", 0)
        
        if soil_type == "sandy" and wind_speed > 20:
            return "high"
        elif soil_type in ["silt", "sandy"] and wind_speed > 15:
            return "moderate"
        else:
            return "low"
    
    def _generate_soil_recommendations(self, soil_type: str, ph_level: float, moisture_content: float) -> list:
        """Generate soil management recommendations"""
        recommendations = []
        
        # pH recommendations
        if ph_level < 6.0:
            recommendations.append("Consider adding lime to raise soil pH")
        elif ph_level > 7.5:
            recommendations.append("Consider adding sulfur to lower soil pH")
        
        # Moisture recommendations
        if moisture_content < 20:
            recommendations.append("Increase irrigation frequency")
        elif moisture_content > 80:
            recommendations.append("Improve drainage to prevent waterlogging")
        
        # Soil type specific recommendations
        if soil_type == "sandy":
            recommendations.append("Add organic matter to improve water retention")
        elif soil_type == "clay":
            recommendations.append("Add organic matter to improve drainage")
        elif soil_type == "loam":
            recommendations.append("Maintain current soil management practices")
        
        return recommendations
    
    async def _get_cached_weather(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Get cached weather data if available and fresh"""
        try:
            db = SessionLocal()
            cached = db.query(WeatherData).filter(
                WeatherData.latitude.between(latitude - 0.01, latitude + 0.01),
                WeatherData.longitude.between(longitude - 0.01, longitude + 0.01),
                WeatherData.expires_at > datetime.utcnow()
            ).first()
            
            if cached:
                return {
                    "current": {
                        "temperature": cached.temperature,
                        "humidity": cached.humidity,
                        "pressure": cached.pressure,
                        "wind_speed": cached.wind_speed,
                        "wind_direction": cached.wind_direction,
                        "description": cached.description,
                        "visibility": cached.visibility,
                        "uv_index": cached.uv_index
                    },
                    "cached": True,
                    "last_updated": cached.created_at.isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached weather: {e}")
            return None
        finally:
            db.close()
    
    async def _cache_weather_data(self, latitude: float, longitude: float, weather_data: Dict):
        """Cache weather data"""
        try:
            db = SessionLocal()
            current = weather_data.get("current", {})
            
            weather_record = WeatherData(
                latitude=latitude,
                longitude=longitude,
                temperature=current.get("temperature"),
                humidity=current.get("humidity"),
                pressure=current.get("pressure"),
                wind_speed=current.get("wind_speed"),
                wind_direction=current.get("wind_direction"),
                description=current.get("description"),
                visibility=current.get("visibility"),
                uv_index=current.get("uv_index"),
                expires_at=datetime.utcnow() + self.cache_duration
            )
            
            db.add(weather_record)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error caching weather data: {e}")
        finally:
            db.close()
    
    async def _get_cached_soil_data(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Get cached soil data if available"""
        try:
            db = SessionLocal()
            cached = db.query(SoilData).filter(
                SoilData.latitude.between(latitude - 0.05, latitude + 0.05),
                SoilData.longitude.between(longitude - 0.05, longitude + 0.05),
                SoilData.expires_at > datetime.utcnow()
            ).first()
            
            if cached:
                return {
                    "ph_level": cached.ph_level,
                    "moisture_content": cached.moisture_content,
                    "nutrients": {
                        "nitrogen": {"value": cached.nitrogen_level, "unit": "mg/kg"},
                        "phosphorus": {"value": cached.phosphorus_level, "unit": "mg/kg"},
                        "potassium": {"value": cached.potassium_level, "unit": "mg/kg"},
                        "organic_matter": {"value": cached.organic_matter, "unit": "%"}
                    },
                    "soil_type": cached.soil_type,
                    "cached": True,
                    "last_updated": cached.created_at.isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached soil data: {e}")
            return None
        finally:
            db.close()
    
    async def _cache_soil_data(self, latitude: float, longitude: float, soil_data: Dict):
        """Cache soil data"""
        try:
            db = SessionLocal()
            nutrients = soil_data.get("nutrients", {})
            
            soil_record = SoilData(
                latitude=latitude,
                longitude=longitude,
                ph_level=soil_data.get("ph_level"),
                moisture_content=soil_data.get("moisture_content"),
                nitrogen_level=nutrients.get("nitrogen", {}).get("value"),
                phosphorus_level=nutrients.get("phosphorus", {}).get("value"),
                potassium_level=nutrients.get("potassium", {}).get("value"),
                organic_matter=nutrients.get("organic_matter", {}).get("value"),
                soil_type=soil_data.get("soil_type"),
                expires_at=datetime.utcnow() + timedelta(days=7)  # Soil data changes slowly
            )
            
            db.add(soil_record)
            db.commit()
            
        except Exception as e:
            logger.error(f"Error caching soil data: {e}")
        finally:
            db.close()
    
    async def _generate_mock_weather_data(self, latitude: float, longitude: float) -> Dict:
        """Generate realistic mock weather data when API is unavailable"""
        import random
        import math
        
        # More realistic temperature based on latitude and time
        now = datetime.utcnow()
        day_of_year = now.timetuple().tm_yday
        hour = now.hour
        
        # Seasonal variation
        seasonal_factor = math.sin((day_of_year - 80) * 2 * math.pi / 365)
        
        # Base temperature varies by latitude
        if abs(latitude) < 23.5:  # Tropical
            base_temp = 28 + seasonal_factor * 4
        elif abs(latitude) < 40:  # Subtropical  
            base_temp = 22 + seasonal_factor * 10
        elif abs(latitude) < 60:  # Temperate
            base_temp = 15 + seasonal_factor * 15
        else:  # Polar
            base_temp = 5 + seasonal_factor * 20
        
        # Daily temperature variation
        daily_variation = 4 * math.sin((hour - 6) * math.pi / 12)
        temperature = base_temp + daily_variation + random.uniform(-3, 3)
        
        # Weather conditions
        conditions = [
            {"name": "Clear", "desc": "Clear sky with sunshine"},
            {"name": "Partly Cloudy", "desc": "Partly cloudy with some sun"},
            {"name": "Cloudy", "desc": "Overcast with clouds"},
            {"name": "Light Rain", "desc": "Light rain showers"},
            {"name": "Sunny", "desc": "Bright sunny weather"}
        ]
        
        condition = random.choice(conditions)
        
        # Humidity based on weather condition
        if condition["name"] in ["Light Rain"]:
            humidity = random.randint(70, 90)
        elif condition["name"] in ["Clear", "Sunny"]:
            humidity = random.randint(30, 60)
        else:
            humidity = random.randint(50, 75)
        
        return {
            "current": {
                "temperature": round(temperature, 1),
                "feels_like": round(temperature + random.uniform(-2, 3), 1),
                "humidity": humidity,
                "pressure": random.randint(1005, 1025),
                "visibility": round(random.uniform(8, 15), 1),
                "uv_index": max(1, min(10, int(8 - abs(latitude)/10 + seasonal_factor * 2))),
                "condition": condition["name"],
                "description": condition["desc"],
                "wind_speed": round(random.uniform(3, 18), 1),
                "wind_direction": random.randint(0, 360)
            },
            "forecast_24h": {
                "temperature_trend": random.choice(["rising", "falling", "stable"]),
                "humidity_trend": random.choice(["rising", "falling", "stable"]),
                "precipitation_chance": random.randint(10, 40),
                "max_temp": round(temperature + random.uniform(3, 8), 1),
                "min_temp": round(temperature - random.uniform(3, 8), 1)
            },
            "agricultural_conditions": {
                "planting_suitability": random.choice(["Excellent", "Good", "Fair", "Poor"]),
                "irrigation_need": random.choice(["Low", "Medium", "High"]),
                "pest_risk": random.choice(["Low", "Medium", "High"]),
                "disease_risk": random.choice(["Low", "Medium", "High"])
            },
            "alerts": self._generate_mock_alerts(temperature, humidity, condition["name"]),
            "mock_data": True,
            "data_source": "🔄 Demo Data (Add WEATHER_API_KEY for real data)",
            "location": f"📍 {latitude:.2f}°, {longitude:.2f}°",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    def _generate_mock_alerts(self, temperature: float, humidity: float, condition: str) -> list:
        """Generate realistic weather alerts"""
        alerts = []
        
        if temperature > 35:
            alerts.append({
                "type": "Heat Warning",
                "severity": "high",
                "message": f"High temperature of {temperature:.1f}°C. Ensure adequate irrigation and shade for crops."
            })
        elif temperature < 5:
            alerts.append({
                "type": "Frost Warning", 
                "severity": "high",
                "message": f"Low temperature of {temperature:.1f}°C. Protect sensitive crops from frost damage."
            })
        
        if humidity > 85:
            alerts.append({
                "type": "High Humidity Alert",
                "severity": "medium", 
                "message": f"High humidity of {humidity}%. Monitor for fungal diseases and improve ventilation."
            })
        elif humidity < 30:
            alerts.append({
                "type": "Low Humidity Alert",
                "severity": "medium",
                "message": f"Low humidity of {humidity}%. Increase irrigation and consider mulching."
            })
        
        if condition == "Light Rain":
            alerts.append({
                "type": "Precipitation Alert",
                "severity": "low",
                "message": "Light rain expected. Good for natural irrigation but monitor soil drainage."
            })
        
        return alerts
    
    async def _get_fallback_weather_data(self, latitude: float, longitude: float) -> Dict:
        """Get fallback weather data"""
        return await self._generate_mock_weather_data(latitude, longitude)
    
    async def _get_fallback_soil_data(self) -> Dict:
        """Get enhanced fallback soil data"""
        import random
        
        # Realistic soil types and their characteristics
        soil_types = ["clay", "sandy", "loam", "silt", "peat"]
        soil_type = random.choice(soil_types)
        
        # pH varies by soil type
        ph_ranges = {
            "clay": (6.0, 7.5),
            "sandy": (5.5, 6.5), 
            "loam": (6.0, 7.0),
            "silt": (6.5, 7.5),
            "peat": (4.5, 6.0)
        }
        
        ph_level = round(random.uniform(*ph_ranges[soil_type]), 1)
        
        # Moisture content varies by soil type
        moisture_ranges = {
            "clay": (40, 70),
            "sandy": (15, 35),
            "loam": (30, 50), 
            "silt": (35, 55),
            "peat": (60, 85)
        }
        
        moisture_content = round(random.uniform(*moisture_ranges[soil_type]), 1)
        
        # Generate nutrient levels
        def get_nutrient_status(value, optimal_range):
            if value < optimal_range[0]:
                return "low"
            elif value > optimal_range[1]:
                return "high"
            else:
                return "optimal"
        
        nitrogen = round(random.uniform(20, 60), 1)
        phosphorus = round(random.uniform(15, 45), 1)
        potassium = round(random.uniform(20, 50), 1)
        organic_matter = round(random.uniform(1.5, 4.5), 1)
        
        # Temperature varies with season and depth
        soil_temp = round(random.uniform(12, 28), 1)
        
        return {
            "soil_type": soil_type,
            "ph_level": ph_level,
            "moisture_content": moisture_content,
            "temperature": soil_temp,
            "nutrients": {
                "nitrogen": {
                    "level": f"{nitrogen} mg/kg",
                    "value": nitrogen,
                    "unit": "mg/kg", 
                    "status": get_nutrient_status(nitrogen, (25, 45))
                },
                "phosphorus": {
                    "level": f"{phosphorus} mg/kg",
                    "value": phosphorus,
                    "unit": "mg/kg",
                    "status": get_nutrient_status(phosphorus, (20, 35))
                },
                "potassium": {
                    "level": f"{potassium} mg/kg", 
                    "value": potassium,
                    "unit": "mg/kg",
                    "status": get_nutrient_status(potassium, (25, 40))
                },
                "organic_matter": {
                    "level": f"{organic_matter}%",
                    "value": organic_matter,
                    "unit": "%",
                    "status": get_nutrient_status(organic_matter, (2.0, 4.0))
                }
            },
            "recommendations": self._generate_soil_recommendations(soil_type, ph_level, moisture_content),
            "compaction_risk": self._assess_compaction_risk(soil_type, moisture_content),
            "erosion_risk": random.choice(["Low", "Medium", "High"]),
            "drainage": {
                "clay": "Poor",
                "sandy": "Excellent", 
                "loam": "Good",
                "silt": "Moderate",
                "peat": "Poor"
            }[soil_type],
            "data_source": "🔄 Demo Data (Add SOIL_API_KEY for real data)",
            "fallback_data": True,
            "last_updated": datetime.utcnow().isoformat()
        }