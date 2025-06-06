"""
Offline Service
Basic offline capabilities and data caching
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from ..core.database import OfflineData, WeatherData, SoilData

logger = logging.getLogger(__name__)

class OfflineService:
    """Service for offline data management and caching"""
    
    def __init__(self):
        # Cache durations for different data types (in hours)
        self.cache_durations = {
            "weather": 6,      # Weather data valid for 6 hours
            "soil": 24,        # Soil data valid for 24 hours
            "disease_tips": 168,  # Disease tips valid for 1 week
            "crop_calendar": 720,  # Crop calendar valid for 1 month
            "farming_tips": 168,   # Farming tips valid for 1 week
            "emergency_contacts": 720,  # Emergency contacts valid for 1 month
        }
        
        # Offline data templates
        self.offline_templates = {
            "disease_tips": self._get_disease_tips_template(),
            "crop_calendar": self._get_crop_calendar_template(),
            "farming_tips": self._get_farming_tips_template(),
            "emergency_contacts": self._get_emergency_contacts_template(),
            "basic_weather": self._get_basic_weather_template(),
            "soil_guidelines": self._get_soil_guidelines_template()
        }
    
    async def cache_data(
        self,
        user_id: int,
        data_type: str,
        data_key: str,
        data_content: Dict[str, Any],
        location_hash: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Cache data for offline use"""
        try:
            # Calculate expiration time
            duration_hours = self.cache_durations.get(data_type, 24)
            expires_at = datetime.now() + timedelta(hours=duration_hours)
            
            # Check if data already exists
            existing_data = db.query(OfflineData).filter(
                OfflineData.user_id == user_id,
                OfflineData.data_type == data_type,
                OfflineData.data_key == data_key
            ).first()
            
            if existing_data:
                # Update existing data
                existing_data.data_content = data_content
                existing_data.expires_at = expires_at
                existing_data.created_at = datetime.now()
            else:
                # Create new cache entry
                offline_data = OfflineData(
                    user_id=user_id,
                    data_type=data_type,
                    data_key=data_key,
                    data_content=data_content,
                    location_hash=location_hash,
                    expires_at=expires_at
                )
                db.add(offline_data)
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Data cached successfully for {duration_hours} hours",
                "expires_at": expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            db.rollback()
            raise
    
    async def get_cached_data(
        self,
        user_id: int,
        data_type: str,
        data_key: Optional[str] = None,
        location_hash: Optional[str] = None,
        db: Session = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached data for offline use"""
        try:
            query = db.query(OfflineData).filter(
                OfflineData.user_id == user_id,
                OfflineData.data_type == data_type,
                OfflineData.expires_at > datetime.now()
            )
            
            if data_key:
                query = query.filter(OfflineData.data_key == data_key)
            
            if location_hash:
                query = query.filter(OfflineData.location_hash == location_hash)
            
            cached_data = query.order_by(OfflineData.created_at.desc()).first()
            
            if cached_data:
                return {
                    "data_type": cached_data.data_type,
                    "data_key": cached_data.data_key,
                    "content": cached_data.data_content,
                    "cached_at": cached_data.created_at.isoformat(),
                    "expires_at": cached_data.expires_at.isoformat(),
                    "is_expired": cached_data.expires_at <= datetime.now()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached data: {str(e)}")
            return None
    
    async def prepare_offline_package(
        self,
        user_id: int,
        latitude: float,
        longitude: float,
        db: Session = None
    ) -> Dict[str, Any]:
        """Prepare a comprehensive offline data package"""
        try:
            location_hash = self._generate_location_hash(latitude, longitude)
            offline_package = {}
            
            # Cache essential offline data
            for data_type, template in self.offline_templates.items():
                await self.cache_data(
                    user_id=user_id,
                    data_type=data_type,
                    data_key=f"{data_type}_{location_hash}",
                    data_content=template,
                    location_hash=location_hash,
                    db=db
                )
                offline_package[data_type] = template
            
            # Try to cache current weather data
            try:
                weather_data = await self._get_current_weather_for_cache(latitude, longitude, db)
                if weather_data:
                    await self.cache_data(
                        user_id=user_id,
                        data_type="weather",
                        data_key=f"weather_{location_hash}",
                        data_content=weather_data,
                        location_hash=location_hash,
                        db=db
                    )
                    offline_package["weather"] = weather_data
            except Exception as e:
                logger.warning(f"Could not cache weather data: {str(e)}")
                offline_package["weather"] = self.offline_templates["basic_weather"]
            
            # Try to cache current soil data
            try:
                soil_data = await self._get_current_soil_for_cache(latitude, longitude, db)
                if soil_data:
                    await self.cache_data(
                        user_id=user_id,
                        data_type="soil",
                        data_key=f"soil_{location_hash}",
                        data_content=soil_data,
                        location_hash=location_hash,
                        db=db
                    )
                    offline_package["soil"] = soil_data
            except Exception as e:
                logger.warning(f"Could not cache soil data: {str(e)}")
                offline_package["soil"] = self.offline_templates["soil_guidelines"]
            
            return {
                "success": True,
                "message": "Offline package prepared successfully",
                "location": {
                    "latitude": latitude,
                    "longitude": longitude,
                    "location_hash": location_hash
                },
                "package_size": len(json.dumps(offline_package)),
                "data_types": list(offline_package.keys()),
                "prepared_at": datetime.now().isoformat(),
                "offline_package": offline_package
            }
            
        except Exception as e:
            logger.error(f"Error preparing offline package: {str(e)}")
            raise
    
    async def get_offline_recommendations(
        self,
        user_id: int,
        crop_type: Optional[str] = None,
        issue_type: Optional[str] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get offline recommendations for farming issues"""
        try:
            recommendations = []
            
            # Get cached farming tips
            farming_tips = await self.get_cached_data(
                user_id=user_id,
                data_type="farming_tips",
                db=db
            )
            
            if farming_tips:
                tips_content = farming_tips["content"]
                
                # Filter recommendations based on crop type and issue
                if crop_type and crop_type.lower() in tips_content.get("crop_specific", {}):
                    recommendations.extend(tips_content["crop_specific"][crop_type.lower()])
                
                if issue_type and issue_type in tips_content.get("issue_specific", {}):
                    recommendations.extend(tips_content["issue_specific"][issue_type])
                
                # Add general recommendations
                recommendations.extend(tips_content.get("general", []))
            
            # Get cached disease tips if relevant
            if issue_type == "disease":
                disease_tips = await self.get_cached_data(
                    user_id=user_id,
                    data_type="disease_tips",
                    db=db
                )
                
                if disease_tips:
                    recommendations.extend(disease_tips["content"].get("general_tips", []))
            
            return {
                "success": True,
                "recommendations": recommendations[:10],  # Limit to top 10
                "source": "offline_cache",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting offline recommendations: {str(e)}")
            return {
                "success": False,
                "recommendations": [],
                "error": str(e)
            }
    
    async def cleanup_expired_cache(self, db: Session = None) -> Dict[str, Any]:
        """Clean up expired cached data"""
        try:
            expired_count = db.query(OfflineData).filter(
                OfflineData.expires_at <= datetime.now()
            ).count()
            
            # Delete expired data
            db.query(OfflineData).filter(
                OfflineData.expires_at <= datetime.now()
            ).delete()
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Cleaned up {expired_count} expired cache entries"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")
            db.rollback()
            raise
    
    async def get_cache_status(
        self,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get status of user's cached data"""
        try:
            cache_entries = db.query(OfflineData).filter(
                OfflineData.user_id == user_id
            ).all()
            
            cache_status = {}
            total_size = 0
            
            for entry in cache_entries:
                data_size = len(json.dumps(entry.data_content))
                total_size += data_size
                
                cache_status[entry.data_type] = {
                    "data_key": entry.data_key,
                    "size_bytes": data_size,
                    "cached_at": entry.created_at.isoformat(),
                    "expires_at": entry.expires_at.isoformat(),
                    "is_expired": entry.expires_at <= datetime.now(),
                    "time_remaining": str(entry.expires_at - datetime.now()) if entry.expires_at > datetime.now() else "Expired"
                }
            
            return {
                "user_id": user_id,
                "total_cache_entries": len(cache_entries),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "cache_details": cache_status,
                "checked_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting cache status: {str(e)}")
            return {}
    
    def _generate_location_hash(self, latitude: float, longitude: float) -> str:
        """Generate a hash for location coordinates"""
        # Round to 2 decimal places for reasonable geographic grouping
        rounded_lat = round(latitude, 2)
        rounded_lng = round(longitude, 2)
        location_string = f"{rounded_lat},{rounded_lng}"
        return hashlib.md5(location_string.encode()).hexdigest()[:8]
    
    async def _get_current_weather_for_cache(
        self,
        latitude: float,
        longitude: float,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Get current weather data for caching"""
        # Try to get from database first
        recent_weather = db.query(WeatherData).filter(
            WeatherData.latitude == latitude,
            WeatherData.longitude == longitude,
            WeatherData.expires_at > datetime.now()
        ).order_by(WeatherData.created_at.desc()).first()
        
        if recent_weather:
            return {
                "temperature": recent_weather.temperature,
                "humidity": recent_weather.humidity,
                "pressure": recent_weather.pressure,
                "wind_speed": recent_weather.wind_speed,
                "description": recent_weather.description,
                "cached_at": recent_weather.created_at.isoformat()
            }
        
        return None
    
    async def _get_current_soil_for_cache(
        self,
        latitude: float,
        longitude: float,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """Get current soil data for caching"""
        # Try to get from database first
        recent_soil = db.query(SoilData).filter(
            SoilData.latitude == latitude,
            SoilData.longitude == longitude,
            SoilData.expires_at > datetime.now()
        ).order_by(SoilData.created_at.desc()).first()
        
        if recent_soil:
            return {
                "ph_level": recent_soil.ph_level,
                "moisture_content": recent_soil.moisture_content,
                "nitrogen_level": recent_soil.nitrogen_level,
                "phosphorus_level": recent_soil.phosphorus_level,
                "potassium_level": recent_soil.potassium_level,
                "soil_type": recent_soil.soil_type,
                "cached_at": recent_soil.created_at.isoformat()
            }
        
        return None
    
    def _get_disease_tips_template(self) -> Dict[str, Any]:
        """Get disease prevention and treatment tips"""
        return {
            "general_tips": [
                "Inspect plants regularly for early disease detection",
                "Ensure proper air circulation around plants",
                "Avoid overhead watering to reduce leaf moisture",
                "Remove and destroy infected plant material immediately",
                "Practice crop rotation to break disease cycles",
                "Use disease-resistant varieties when available",
                "Maintain proper plant spacing to reduce humidity",
                "Apply organic fungicides preventively during humid conditions"
            ],
            "common_diseases": {
                "blight": {
                    "symptoms": "Brown or black spots on leaves, stems wilting",
                    "treatment": "Remove affected parts, improve air circulation, apply copper fungicide",
                    "prevention": "Avoid overhead watering, ensure good drainage"
                },
                "powdery_mildew": {
                    "symptoms": "White powdery coating on leaves",
                    "treatment": "Spray with baking soda solution (1 tsp per quart water)",
                    "prevention": "Ensure good air circulation, avoid overcrowding"
                },
                "root_rot": {
                    "symptoms": "Yellowing leaves, stunted growth, mushy roots",
                    "treatment": "Improve drainage, reduce watering, remove affected plants",
                    "prevention": "Ensure proper drainage, avoid overwatering"
                }
            },
            "organic_treatments": [
                "Neem oil spray for fungal infections",
                "Baking soda solution for powdery mildew",
                "Copper sulfate for bacterial diseases",
                "Compost tea for general plant health",
                "Garlic and chili spray for pest deterrent"
            ]
        }
    
    def _get_crop_calendar_template(self) -> Dict[str, Any]:
        """Get seasonal crop calendar"""
        return {
            "spring": {
                "plant": ["tomatoes", "peppers", "cucumbers", "beans", "corn"],
                "harvest": ["lettuce", "spinach", "radishes", "peas"],
                "tasks": ["soil preparation", "seed starting", "transplanting", "mulching"]
            },
            "summer": {
                "plant": ["lettuce", "spinach", "carrots", "beets"],
                "harvest": ["tomatoes", "peppers", "cucumbers", "beans", "corn"],
                "tasks": ["watering", "pest control", "pruning", "harvesting"]
            },
            "fall": {
                "plant": ["garlic", "onions", "winter vegetables"],
                "harvest": ["root vegetables", "winter squash", "late tomatoes"],
                "tasks": ["soil amendment", "cover crop planting", "tool maintenance"]
            },
            "winter": {
                "plant": ["indoor herbs", "microgreens"],
                "harvest": ["stored crops", "winter vegetables"],
                "tasks": ["planning", "seed ordering", "equipment maintenance", "education"]
            },
            "monthly_tasks": {
                "january": "Plan garden layout, order seeds, maintain tools",
                "february": "Start seeds indoors, prepare soil amendments",
                "march": "Direct sow cool-season crops, transplant seedlings",
                "april": "Plant warm-season crops, mulch beds",
                "may": "Continue planting, monitor for pests",
                "june": "Harvest early crops, maintain irrigation",
                "july": "Peak harvest season, preserve surplus",
                "august": "Plant fall crops, continue harvesting",
                "september": "Harvest and preserve, plant cover crops",
                "october": "Final harvest, clean up garden beds",
                "november": "Protect plants from frost, plan next year",
                "december": "Rest period, review and plan"
            }
        }
    
    def _get_farming_tips_template(self) -> Dict[str, Any]:
        """Get general farming tips and best practices"""
        return {
            "general": [
                "Test soil pH annually and amend as needed",
                "Rotate crops to prevent soil depletion and disease buildup",
                "Compost organic matter to improve soil health",
                "Water deeply but less frequently to encourage deep roots",
                "Mulch around plants to retain moisture and suppress weeds",
                "Keep detailed records of planting dates and varieties",
                "Learn to identify beneficial insects and encourage them",
                "Start small and expand gradually as you gain experience"
            ],
            "crop_specific": {
                "tomatoes": [
                    "Provide support with cages or stakes",
                    "Remove suckers for better fruit production",
                    "Water consistently to prevent blossom end rot",
                    "Mulch heavily to maintain soil moisture"
                ],
                "peppers": [
                    "Plant in warm soil after frost danger passes",
                    "Provide consistent moisture but avoid overwatering",
                    "Support heavy-fruited varieties",
                    "Harvest regularly to encourage continued production"
                ],
                "lettuce": [
                    "Plant in cool weather for best quality",
                    "Provide afternoon shade in hot climates",
                    "Harvest outer leaves for continuous production",
                    "Succession plant every 2 weeks"
                ]
            },
            "issue_specific": {
                "pest": [
                    "Encourage beneficial insects with diverse plantings",
                    "Use row covers to protect young plants",
                    "Hand-pick larger pests when possible",
                    "Apply organic pesticides only when necessary"
                ],
                "disease": [
                    "Ensure good air circulation around plants",
                    "Water at soil level to keep leaves dry",
                    "Remove infected plant material immediately",
                    "Practice crop rotation to break disease cycles"
                ],
                "watering": [
                    "Water early morning to reduce evaporation",
                    "Check soil moisture before watering",
                    "Use drip irrigation or soaker hoses when possible",
                    "Mulch to retain soil moisture"
                ]
            }
        }
    
    def _get_emergency_contacts_template(self) -> Dict[str, Any]:
        """Get emergency contacts and resources"""
        return {
            "agricultural_extension": {
                "description": "Local agricultural extension office",
                "services": ["Soil testing", "Pest identification", "Crop advice"],
                "contact_info": "Contact your local county extension office"
            },
            "veterinary_services": {
                "description": "Emergency veterinary services for livestock",
                "services": ["Animal health", "Emergency treatment", "Vaccination"],
                "contact_info": "Locate nearest large animal veterinarian"
            },
            "weather_services": {
                "description": "Weather alerts and forecasts",
                "services": ["Severe weather warnings", "Frost alerts", "Precipitation forecasts"],
                "contact_info": "National Weather Service or local weather station"
            },
            "equipment_repair": {
                "description": "Farm equipment repair services",
                "services": ["Tractor repair", "Irrigation system repair", "Tool maintenance"],
                "contact_info": "Local equipment dealers and repair shops"
            },
            "emergency_numbers": {
                "fire_department": "911 or local fire department",
                "poison_control": "1-800-222-1222 (US)",
                "animal_poison_control": "1-888-426-4435 (US)"
            }
        }
    
    def _get_basic_weather_template(self) -> Dict[str, Any]:
        """Get basic weather information template"""
        return {
            "note": "This is cached weather data. For current conditions, connect to internet.",
            "general_guidelines": {
                "temperature": "Monitor daily highs and lows for planting decisions",
                "humidity": "High humidity increases disease risk",
                "wind": "Strong winds can damage plants and increase water needs",
                "precipitation": "Track rainfall for irrigation planning"
            },
            "seasonal_averages": {
                "spring": {"temp_range": "15-25°C", "rainfall": "Moderate"},
                "summer": {"temp_range": "20-35°C", "rainfall": "Variable"},
                "fall": {"temp_range": "10-20°C", "rainfall": "Increasing"},
                "winter": {"temp_range": "0-15°C", "rainfall": "High"}
            }
        }
    
    def _get_soil_guidelines_template(self) -> Dict[str, Any]:
        """Get soil management guidelines"""
        return {
            "ph_guidelines": {
                "acidic": "pH < 6.0 - Add lime to raise pH",
                "neutral": "pH 6.0-7.5 - Ideal for most crops",
                "alkaline": "pH > 7.5 - Add sulfur or organic matter to lower pH"
            },
            "nutrient_management": {
                "nitrogen": "Essential for leaf growth, deficiency causes yellowing",
                "phosphorus": "Important for root development and flowering",
                "potassium": "Helps with disease resistance and fruit quality"
            },
            "soil_improvement": [
                "Add organic compost annually",
                "Avoid working wet soil to prevent compaction",
                "Use cover crops to add organic matter",
                "Test soil every 2-3 years",
                "Maintain proper drainage"
            ],
            "soil_types": {
                "clay": "Heavy soil, retains water, may need drainage improvement",
                "sandy": "Light soil, drains quickly, may need more frequent watering",
                "loam": "Ideal soil type, good drainage and water retention"
            }
        }