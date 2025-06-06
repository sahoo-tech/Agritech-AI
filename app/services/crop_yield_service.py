"""
Crop Yield Prediction Service
Advanced analytics for crop yield forecasting
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import logging
from sqlalchemy.orm import Session

from ..core.database import CropYieldPrediction, WeatherData, SoilData
from .weather_service import WeatherService

logger = logging.getLogger(__name__)

class CropYieldService:
    """Service for crop yield prediction and analytics"""
    
    def __init__(self):
        self.weather_service = WeatherService()
        
        # Crop-specific parameters for yield prediction
        self.crop_parameters = {
            "wheat": {
                "optimal_temp_range": (15, 25),
                "optimal_humidity_range": (60, 80),
                "growing_days": 120,
                "water_requirement": 450,  # mm
                "base_yield_per_hectare": 3000,  # kg
                "temp_sensitivity": 0.8,
                "humidity_sensitivity": 0.6,
                "soil_ph_optimal": (6.0, 7.5)
            },
            "rice": {
                "optimal_temp_range": (20, 30),
                "optimal_humidity_range": (70, 90),
                "growing_days": 150,
                "water_requirement": 1200,  # mm
                "base_yield_per_hectare": 4000,  # kg
                "temp_sensitivity": 0.9,
                "humidity_sensitivity": 0.8,
                "soil_ph_optimal": (5.5, 7.0)
            },
            "corn": {
                "optimal_temp_range": (18, 27),
                "optimal_humidity_range": (65, 85),
                "growing_days": 100,
                "water_requirement": 500,  # mm
                "base_yield_per_hectare": 5000,  # kg
                "temp_sensitivity": 0.7,
                "humidity_sensitivity": 0.5,
                "soil_ph_optimal": (6.0, 7.0)
            },
            "soybeans": {
                "optimal_temp_range": (20, 30),
                "optimal_humidity_range": (60, 80),
                "growing_days": 110,
                "water_requirement": 450,  # mm
                "base_yield_per_hectare": 2500,  # kg
                "temp_sensitivity": 0.6,
                "humidity_sensitivity": 0.7,
                "soil_ph_optimal": (6.0, 7.5)
            },
            "tomatoes": {
                "optimal_temp_range": (18, 26),
                "optimal_humidity_range": (65, 85),
                "growing_days": 80,
                "water_requirement": 400,  # mm
                "base_yield_per_hectare": 40000,  # kg
                "temp_sensitivity": 0.9,
                "humidity_sensitivity": 0.8,
                "soil_ph_optimal": (6.0, 7.0)
            }
        }
    
    async def predict_crop_yield(
        self,
        crop_type: str,
        field_size_hectares: float,
        planting_date: datetime,
        latitude: float,
        longitude: float,
        soil_data: Optional[Dict] = None,
        historical_weather: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Predict crop yield based on various factors
        """
        try:
            crop_type = crop_type.lower()
            if crop_type not in self.crop_parameters:
                raise ValueError(f"Crop type '{crop_type}' not supported")
            
            crop_params = self.crop_parameters[crop_type]
            
            # Calculate expected harvest date
            harvest_date = planting_date + timedelta(days=crop_params["growing_days"])
            
            # Get weather forecast for growing period
            weather_factors = await self._analyze_weather_factors(
                latitude, longitude, planting_date, harvest_date, crop_params
            )
            
            # Analyze soil factors
            soil_factors = await self._analyze_soil_factors(
                latitude, longitude, crop_params, soil_data
            )
            
            # Calculate base yield
            base_yield = crop_params["base_yield_per_hectare"] * field_size_hectares
            
            # Apply weather impact
            weather_impact = self._calculate_weather_impact(weather_factors, crop_params)
            
            # Apply soil impact
            soil_impact = self._calculate_soil_impact(soil_factors, crop_params)
            
            # Calculate final predicted yield
            predicted_yield = base_yield * weather_impact * soil_impact
            
            # Calculate confidence score
            confidence_score = self._calculate_confidence_score(
                weather_factors, soil_factors, crop_params
            )
            
            # Generate recommendations
            recommendations = self._generate_yield_recommendations(
                weather_factors, soil_factors, crop_params
            )
            
            return {
                "crop_type": crop_type,
                "field_size_hectares": field_size_hectares,
                "planting_date": planting_date.isoformat(),
                "expected_harvest_date": harvest_date.isoformat(),
                "predicted_yield_kg": round(predicted_yield, 2),
                "predicted_yield_per_hectare": round(predicted_yield / field_size_hectares, 2),
                "confidence_score": round(confidence_score, 2),
                "weather_impact_factor": round(weather_impact, 2),
                "soil_impact_factor": round(soil_impact, 2),
                "weather_factors": weather_factors,
                "soil_factors": soil_factors,
                "recommendations": recommendations,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error predicting crop yield: {str(e)}")
            raise
    
    async def _analyze_weather_factors(
        self,
        latitude: float,
        longitude: float,
        planting_date: datetime,
        harvest_date: datetime,
        crop_params: Dict
    ) -> Dict[str, Any]:
        """Analyze weather factors for yield prediction"""
        
        # Get current weather data
        current_weather = await self.weather_service.get_weather_data(latitude, longitude)
        
        # Simulate weather analysis for growing period
        # In a real implementation, this would use historical data and forecasts
        avg_temp = current_weather.get("current", {}).get("temperature", 20)
        avg_humidity = current_weather.get("current", {}).get("humidity", 70)
        
        # Calculate temperature suitability
        optimal_temp_min, optimal_temp_max = crop_params["optimal_temp_range"]
        temp_suitability = self._calculate_range_suitability(
            avg_temp, optimal_temp_min, optimal_temp_max
        )
        
        # Calculate humidity suitability
        optimal_humidity_min, optimal_humidity_max = crop_params["optimal_humidity_range"]
        humidity_suitability = self._calculate_range_suitability(
            avg_humidity, optimal_humidity_min, optimal_humidity_max
        )
        
        return {
            "average_temperature": avg_temp,
            "average_humidity": avg_humidity,
            "temperature_suitability": temp_suitability,
            "humidity_suitability": humidity_suitability,
            "growing_days": (harvest_date - planting_date).days,
            "weather_stress_days": max(0, 10 - temp_suitability * 10),  # Simulated
            "rainfall_adequacy": 0.8  # Simulated
        }
    
    async def _analyze_soil_factors(
        self,
        latitude: float,
        longitude: float,
        crop_params: Dict,
        soil_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Analyze soil factors for yield prediction"""
        
        if not soil_data:
            # Get soil data from service
            soil_response = await self.weather_service.get_soil_data(latitude, longitude)
            soil_data = soil_response or {}
        
        # Extract soil parameters
        ph_level = soil_data.get("ph_level", 6.5)
        nitrogen = soil_data.get("nutrients", {}).get("nitrogen", "Medium")
        phosphorus = soil_data.get("nutrients", {}).get("phosphorus", "Medium")
        potassium = soil_data.get("nutrients", {}).get("potassium", "Medium")
        moisture = soil_data.get("moisture_content", 50)
        
        # Calculate pH suitability
        optimal_ph_min, optimal_ph_max = crop_params["soil_ph_optimal"]
        ph_suitability = self._calculate_range_suitability(
            ph_level, optimal_ph_min, optimal_ph_max
        )
        
        # Convert nutrient levels to numeric scores
        nutrient_scores = {
            "Low": 0.6,
            "Medium": 0.8,
            "High": 1.0
        }
        
        nitrogen_score = nutrient_scores.get(nitrogen, 0.8)
        phosphorus_score = nutrient_scores.get(phosphorus, 0.8)
        potassium_score = nutrient_scores.get(potassium, 0.8)
        
        # Calculate overall soil fertility
        soil_fertility = (nitrogen_score + phosphorus_score + potassium_score) / 3
        
        return {
            "ph_level": ph_level,
            "ph_suitability": ph_suitability,
            "nitrogen_level": nitrogen,
            "phosphorus_level": phosphorus,
            "potassium_level": potassium,
            "moisture_content": moisture,
            "soil_fertility_score": soil_fertility,
            "drainage_quality": 0.8,  # Simulated
            "organic_matter_content": 0.7  # Simulated
        }
    
    def _calculate_range_suitability(self, value: float, min_optimal: float, max_optimal: float) -> float:
        """Calculate suitability score for a value within an optimal range"""
        if min_optimal <= value <= max_optimal:
            return 1.0
        elif value < min_optimal:
            # Linear decrease below optimal range
            return max(0.0, 1.0 - (min_optimal - value) / min_optimal)
        else:
            # Linear decrease above optimal range
            return max(0.0, 1.0 - (value - max_optimal) / max_optimal)
    
    def _calculate_weather_impact(self, weather_factors: Dict, crop_params: Dict) -> float:
        """Calculate weather impact on yield"""
        temp_impact = weather_factors["temperature_suitability"] * crop_params["temp_sensitivity"]
        humidity_impact = weather_factors["humidity_suitability"] * crop_params["humidity_sensitivity"]
        rainfall_impact = weather_factors["rainfall_adequacy"]
        
        # Combine factors with weights
        weather_impact = (
            temp_impact * 0.4 +
            humidity_impact * 0.3 +
            rainfall_impact * 0.3
        )
        
        return max(0.3, min(1.5, weather_impact))  # Clamp between 0.3 and 1.5
    
    def _calculate_soil_impact(self, soil_factors: Dict, crop_params: Dict) -> float:
        """Calculate soil impact on yield"""
        ph_impact = soil_factors["ph_suitability"]
        fertility_impact = soil_factors["soil_fertility_score"]
        drainage_impact = soil_factors["drainage_quality"]
        
        # Combine factors with weights
        soil_impact = (
            ph_impact * 0.3 +
            fertility_impact * 0.5 +
            drainage_impact * 0.2
        )
        
        return max(0.4, min(1.3, soil_impact))  # Clamp between 0.4 and 1.3
    
    def _calculate_confidence_score(
        self,
        weather_factors: Dict,
        soil_factors: Dict,
        crop_params: Dict
    ) -> float:
        """Calculate confidence score for the prediction"""
        
        # Base confidence
        confidence = 0.7
        
        # Adjust based on data quality
        if weather_factors["temperature_suitability"] > 0.8:
            confidence += 0.1
        if soil_factors["ph_suitability"] > 0.8:
            confidence += 0.1
        if soil_factors["soil_fertility_score"] > 0.8:
            confidence += 0.1
        
        return min(0.95, confidence)  # Cap at 95%
    
    def _generate_yield_recommendations(
        self,
        weather_factors: Dict,
        soil_factors: Dict,
        crop_params: Dict
    ) -> List[str]:
        """Generate recommendations to improve yield"""
        recommendations = []
        
        # Temperature recommendations
        if weather_factors["temperature_suitability"] < 0.7:
            recommendations.append(
                "Consider using shade nets or greenhouse cultivation to optimize temperature"
            )
        
        # Humidity recommendations
        if weather_factors["humidity_suitability"] < 0.7:
            recommendations.append(
                "Implement proper irrigation and mulching to maintain optimal humidity"
            )
        
        # Soil pH recommendations
        if soil_factors["ph_suitability"] < 0.7:
            if soil_factors["ph_level"] < crop_params["soil_ph_optimal"][0]:
                recommendations.append(
                    "Apply lime to increase soil pH for better nutrient availability"
                )
            else:
                recommendations.append(
                    "Apply sulfur or organic matter to decrease soil pH"
                )
        
        # Nutrient recommendations
        if soil_factors["soil_fertility_score"] < 0.8:
            recommendations.append(
                "Apply balanced fertilizer to improve soil nutrient levels"
            )
        
        # General recommendations
        recommendations.extend([
            "Monitor crop regularly for pests and diseases",
            "Ensure adequate water supply during critical growth stages",
            "Consider crop rotation to maintain soil health"
        ])
        
        return recommendations
    
    async def get_historical_yield_data(
        self,
        user_id: int,
        crop_type: Optional[str] = None,
        db: Session = None
    ) -> List[Dict]:
        """Get historical yield predictions for analysis"""
        try:
            query = db.query(CropYieldPrediction).filter(
                CropYieldPrediction.user_id == user_id
            )
            
            if crop_type:
                query = query.filter(CropYieldPrediction.crop_type == crop_type.lower())
            
            predictions = query.order_by(CropYieldPrediction.created_at.desc()).limit(20).all()
            
            return [
                {
                    "id": pred.id,
                    "crop_type": pred.crop_type,
                    "field_size_hectares": pred.field_size_hectares,
                    "planting_date": pred.planting_date.isoformat(),
                    "predicted_yield_kg": pred.predicted_yield_kg,
                    "confidence_score": pred.confidence_score,
                    "created_at": pred.created_at.isoformat()
                }
                for pred in predictions
            ]
            
        except Exception as e:
            logger.error(f"Error getting historical yield data: {str(e)}")
            return []
    
    def get_supported_crops(self) -> List[Dict[str, Any]]:
        """Get list of supported crops with their parameters"""
        return [
            {
                "name": crop_name,
                "display_name": crop_name.title(),
                "growing_days": params["growing_days"],
                "optimal_temperature": f"{params['optimal_temp_range'][0]}-{params['optimal_temp_range'][1]}°C",
                "water_requirement": f"{params['water_requirement']} mm",
                "base_yield": f"{params['base_yield_per_hectare']} kg/hectare"
            }
            for crop_name, params in self.crop_parameters.items()
        ]