"""
Precision Agriculture Service
Provides advanced field management, variable rate applications, and precision monitoring
"""

import json
import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from geopy.distance import geodesic
import logging

logger = logging.getLogger(__name__)

class PrecisionAgricultureService:
    """Service for precision agriculture operations"""
    
    def __init__(self):
        """Initialize the precision agriculture service"""
        self.ndvi_thresholds = {
            "poor": 0.3,
            "fair": 0.5,
            "good": 0.7,
            "excellent": 0.9
        }
        
        self.soil_zones = {
            "sandy": {"drainage": "excellent", "water_holding": "low", "nutrient_retention": "low"},
            "loamy": {"drainage": "good", "water_holding": "medium", "nutrient_retention": "high"},
            "clay": {"drainage": "poor", "water_holding": "high", "nutrient_retention": "high"},
            "silty": {"drainage": "fair", "water_holding": "medium", "nutrient_retention": "medium"}
        }
    
    async def create_field_map(self, field_data: Dict) -> Dict:
        """Create a comprehensive field map with management zones"""
        try:
            field_boundaries = field_data.get("boundaries", [])
            elevation_data = field_data.get("elevation_data", [])
            soil_samples = field_data.get("soil_samples", [])
            
            # Calculate field area
            area_hectares = self._calculate_field_area(field_boundaries)
            
            # Generate management zones
            management_zones = await self._generate_management_zones(
                field_boundaries, elevation_data, soil_samples
            )
            
            # Create drainage analysis
            drainage_patterns = self._analyze_drainage_patterns(
                field_boundaries, elevation_data
            )
            
            # Generate soil zones
            soil_zones = self._create_soil_zones(soil_samples, field_boundaries)
            
            return {
                "field_map": {
                    "boundaries": field_boundaries,
                    "area_hectares": area_hectares,
                    "management_zones": management_zones,
                    "soil_zones": soil_zones,
                    "drainage_patterns": drainage_patterns,
                    "elevation_analysis": self._analyze_elevation(elevation_data),
                    "created_at": datetime.utcnow().isoformat()
                },
                "recommendations": self._generate_field_recommendations(
                    management_zones, soil_zones, drainage_patterns
                )
            }
            
        except Exception as e:
            logger.error(f"Error creating field map: {str(e)}")
            return {"error": f"Failed to create field map: {str(e)}"}
    
    async def plan_variable_rate_application(self, application_data: Dict) -> Dict:
        """Plan variable rate application based on field conditions"""
        try:
            field_zones = application_data.get("field_zones", [])
            application_type = application_data.get("type", "fertilizer")
            target_crop = application_data.get("crop_type", "corn")
            soil_test_results = application_data.get("soil_tests", [])
            
            # Generate application rate map
            rate_map = await self._generate_application_rates(
                field_zones, application_type, target_crop, soil_test_results
            )
            
            # Calculate total quantities and costs
            quantities = self._calculate_application_quantities(rate_map)
            
            # Generate application timing recommendations
            timing_recommendations = self._get_application_timing(
                application_type, target_crop
            )
            
            # Equipment recommendations
            equipment_recommendations = self._recommend_equipment(
                application_type, quantities["total_area"]
            )
            
            return {
                "application_plan": {
                    "type": application_type,
                    "crop": target_crop,
                    "rate_map": rate_map,
                    "total_quantities": quantities,
                    "timing": timing_recommendations,
                    "equipment": equipment_recommendations,
                    "estimated_cost": self._calculate_application_cost(
                        quantities, application_type
                    ),
                    "created_at": datetime.utcnow().isoformat()
                },
                "optimization_notes": self._generate_optimization_notes(rate_map)
            }
            
        except Exception as e:
            logger.error(f"Error planning variable rate application: {str(e)}")
            return {"error": f"Failed to plan application: {str(e)}"}
    
    async def analyze_field_monitoring_data(self, monitoring_data: Dict) -> Dict:
        """Analyze field monitoring data from various sources"""
        try:
            data_type = monitoring_data.get("type", "ndvi")
            data_points = monitoring_data.get("data_points", [])
            field_boundaries = monitoring_data.get("field_boundaries", [])
            measurement_date = monitoring_data.get("date", datetime.utcnow().isoformat())
            
            # Analyze based on data type
            if data_type == "ndvi":
                analysis = await self._analyze_ndvi_data(data_points, field_boundaries)
            elif data_type == "soil_moisture":
                analysis = await self._analyze_soil_moisture_data(data_points, field_boundaries)
            elif data_type == "temperature":
                analysis = await self._analyze_temperature_data(data_points, field_boundaries)
            elif data_type == "growth_stage":
                analysis = await self._analyze_growth_stage_data(data_points, field_boundaries)
            else:
                analysis = await self._analyze_generic_data(data_points, field_boundaries)
            
            # Detect anomalies
            anomalies = self._detect_field_anomalies(data_points, data_type)
            
            # Generate recommendations
            recommendations = self._generate_monitoring_recommendations(
                analysis, anomalies, data_type
            )
            
            return {
                "monitoring_analysis": {
                    "type": data_type,
                    "measurement_date": measurement_date,
                    "analysis_results": analysis,
                    "anomalies_detected": anomalies,
                    "field_statistics": self._calculate_field_statistics(data_points),
                    "spatial_patterns": self._identify_spatial_patterns(data_points),
                    "recommendations": recommendations,
                    "next_monitoring_date": self._suggest_next_monitoring_date(data_type),
                    "analyzed_at": datetime.utcnow().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing monitoring data: {str(e)}")
            return {"error": f"Failed to analyze monitoring data: {str(e)}"}
    
    async def generate_yield_prediction_map(self, field_data: Dict) -> Dict:
        """Generate spatial yield prediction map"""
        try:
            field_zones = field_data.get("management_zones", [])
            historical_yields = field_data.get("historical_yields", [])
            current_season_data = field_data.get("current_season", {})
            crop_type = field_data.get("crop_type", "corn")
            
            # Generate yield predictions for each zone
            yield_predictions = []
            for zone in field_zones:
                zone_prediction = await self._predict_zone_yield(
                    zone, historical_yields, current_season_data, crop_type
                )
                yield_predictions.append(zone_prediction)
            
            # Calculate field-level statistics
            field_stats = self._calculate_yield_statistics(yield_predictions)
            
            # Generate yield variability map
            variability_map = self._create_yield_variability_map(yield_predictions)
            
            # Risk assessment
            risk_assessment = self._assess_yield_risks(
                yield_predictions, current_season_data
            )
            
            return {
                "yield_prediction": {
                    "crop_type": crop_type,
                    "prediction_date": datetime.utcnow().isoformat(),
                    "zone_predictions": yield_predictions,
                    "field_statistics": field_stats,
                    "variability_map": variability_map,
                    "risk_assessment": risk_assessment,
                    "confidence_level": self._calculate_prediction_confidence(
                        historical_yields, current_season_data
                    ),
                    "factors_considered": [
                        "soil_quality", "weather_patterns", "management_practices",
                        "historical_performance", "current_crop_health"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating yield prediction: {str(e)}")
            return {"error": f"Failed to generate yield prediction: {str(e)}"}
    
    def _calculate_field_area(self, boundaries: List[List[float]]) -> float:
        """Calculate field area in hectares using polygon coordinates"""
        if len(boundaries) < 3:
            return 0.0
        
        # Use shoelace formula for polygon area
        area_m2 = 0.0
        n = len(boundaries)
        
        for i in range(n):
            j = (i + 1) % n
            # Convert lat/lng to approximate meters (rough calculation)
            lat1, lng1 = boundaries[i]
            lat2, lng2 = boundaries[j]
            
            # Approximate conversion (not precise for large areas)
            x1 = lng1 * 111320 * math.cos(math.radians(lat1))
            y1 = lat1 * 110540
            x2 = lng2 * 111320 * math.cos(math.radians(lat2))
            y2 = lat2 * 110540
            
            area_m2 += x1 * y2 - x2 * y1
        
        area_m2 = abs(area_m2) / 2.0
        return area_m2 / 10000  # Convert to hectares
    
    async def _generate_management_zones(self, boundaries: List, elevation_data: List, 
                                       soil_samples: List) -> List[Dict]:
        """Generate management zones based on field characteristics"""
        zones = []
        
        # Simple zone generation based on elevation and soil data
        if elevation_data and soil_samples:
            # Create zones based on elevation quartiles
            elevations = [point.get("elevation", 0) for point in elevation_data]
            if elevations:
                q1 = np.percentile(elevations, 25)
                q2 = np.percentile(elevations, 50)
                q3 = np.percentile(elevations, 75)
                
                zones = [
                    {
                        "zone_id": "low_elevation",
                        "name": "Low Elevation Zone",
                        "elevation_range": [min(elevations), q1],
                        "characteristics": ["good_drainage", "lower_water_retention"],
                        "management_recommendations": ["increased_irrigation", "nitrogen_management"]
                    },
                    {
                        "zone_id": "medium_low_elevation",
                        "name": "Medium-Low Elevation Zone",
                        "elevation_range": [q1, q2],
                        "characteristics": ["moderate_drainage", "medium_water_retention"],
                        "management_recommendations": ["balanced_fertilization", "standard_practices"]
                    },
                    {
                        "zone_id": "medium_high_elevation",
                        "name": "Medium-High Elevation Zone",
                        "elevation_range": [q2, q3],
                        "characteristics": ["moderate_drainage", "good_water_retention"],
                        "management_recommendations": ["phosphorus_focus", "erosion_control"]
                    },
                    {
                        "zone_id": "high_elevation",
                        "name": "High Elevation Zone",
                        "elevation_range": [q3, max(elevations)],
                        "characteristics": ["poor_drainage", "high_water_retention"],
                        "management_recommendations": ["drainage_improvement", "reduced_irrigation"]
                    }
                ]
        else:
            # Default single zone
            zones = [{
                "zone_id": "uniform",
                "name": "Uniform Management Zone",
                "characteristics": ["standard_conditions"],
                "management_recommendations": ["standard_practices"]
            }]
        
        return zones
    
    def _analyze_drainage_patterns(self, boundaries: List, elevation_data: List) -> Dict:
        """Analyze field drainage patterns"""
        if not elevation_data:
            return {"status": "no_elevation_data", "patterns": []}
        
        elevations = [point.get("elevation", 0) for point in elevation_data]
        
        return {
            "overall_slope": (max(elevations) - min(elevations)) / len(elevations),
            "drainage_quality": "good" if max(elevations) - min(elevations) > 5 else "poor",
            "water_accumulation_areas": self._identify_low_areas(elevation_data),
            "erosion_risk_areas": self._identify_steep_areas(elevation_data),
            "recommendations": [
                "Install drainage tiles in low areas",
                "Implement contour farming on slopes",
                "Consider terracing for steep areas"
            ]
        }
    
    def _create_soil_zones(self, soil_samples: List, boundaries: List) -> List[Dict]:
        """Create soil management zones"""
        if not soil_samples:
            return [{"zone": "default", "soil_type": "unknown", "management": "standard"}]
        
        zones = []
        for i, sample in enumerate(soil_samples):
            zone = {
                "zone_id": f"soil_zone_{i+1}",
                "location": sample.get("location", [0, 0]),
                "soil_type": sample.get("soil_type", "loamy"),
                "ph_level": sample.get("ph", 6.5),
                "organic_matter": sample.get("organic_matter", 3.0),
                "nutrients": {
                    "nitrogen": sample.get("nitrogen", 20),
                    "phosphorus": sample.get("phosphorus", 15),
                    "potassium": sample.get("potassium", 150)
                },
                "management_recommendations": self._get_soil_management_recommendations(sample)
            }
            zones.append(zone)
        
        return zones
    
    def _analyze_elevation(self, elevation_data: List) -> Dict:
        """Analyze elevation data for field insights"""
        if not elevation_data:
            return {"status": "no_data"}
        
        elevations = [point.get("elevation", 0) for point in elevation_data]
        
        return {
            "min_elevation": min(elevations),
            "max_elevation": max(elevations),
            "average_elevation": sum(elevations) / len(elevations),
            "elevation_variance": np.var(elevations),
            "slope_analysis": {
                "gentle_slopes": len([e for e in elevations if abs(e - np.mean(elevations)) < 2]),
                "moderate_slopes": len([e for e in elevations if 2 <= abs(e - np.mean(elevations)) < 5]),
                "steep_slopes": len([e for e in elevations if abs(e - np.mean(elevations)) >= 5])
            }
        }
    
    def _generate_field_recommendations(self, management_zones: List, soil_zones: List, 
                                      drainage_patterns: Dict) -> List[str]:
        """Generate field management recommendations"""
        recommendations = []
        
        # Zone-based recommendations
        if len(management_zones) > 1:
            recommendations.append("Implement zone-specific management practices")
            recommendations.append("Use variable rate application for fertilizers")
        
        # Drainage recommendations
        if drainage_patterns.get("drainage_quality") == "poor":
            recommendations.append("Install drainage systems in low-lying areas")
            recommendations.append("Consider raised beds for better drainage")
        
        # Soil recommendations
        if soil_zones:
            avg_ph = sum(zone.get("ph_level", 6.5) for zone in soil_zones) / len(soil_zones)
            if avg_ph < 6.0:
                recommendations.append("Apply lime to increase soil pH")
            elif avg_ph > 7.5:
                recommendations.append("Apply sulfur to decrease soil pH")
        
        recommendations.extend([
            "Monitor crop health regularly using NDVI imagery",
            "Implement precision irrigation based on soil moisture",
            "Use GPS-guided equipment for accurate applications",
            "Keep detailed records of all field operations"
        ])
        
        return recommendations
    
    async def _generate_application_rates(self, field_zones: List, app_type: str, 
                                        crop: str, soil_tests: List) -> List[Dict]:
        """Generate variable application rate map"""
        rate_map = []
        
        base_rates = {
            "fertilizer": {"corn": 150, "soybean": 100, "wheat": 120},
            "pesticide": {"corn": 2.5, "soybean": 2.0, "wheat": 2.2},
            "seed": {"corn": 75000, "soybean": 350000, "wheat": 4500000},
            "water": {"corn": 25, "soybean": 20, "wheat": 22}
        }
        
        base_rate = base_rates.get(app_type, {}).get(crop, 100)
        
        for zone in field_zones:
            # Adjust rate based on zone characteristics
            rate_modifier = 1.0
            
            if "poor_drainage" in zone.get("characteristics", []):
                rate_modifier *= 0.8  # Reduce rate in poorly drained areas
            elif "good_drainage" in zone.get("characteristics", []):
                rate_modifier *= 1.1  # Increase rate in well-drained areas
            
            zone_rate = {
                "zone_id": zone.get("zone_id", "unknown"),
                "application_rate": base_rate * rate_modifier,
                "unit": self._get_application_unit(app_type),
                "justification": self._get_rate_justification(zone, rate_modifier)
            }
            rate_map.append(zone_rate)
        
        return rate_map
    
    def _calculate_application_quantities(self, rate_map: List[Dict]) -> Dict:
        """Calculate total application quantities"""
        total_rate = sum(zone.get("application_rate", 0) for zone in rate_map)
        total_area = len(rate_map)  # Simplified - should use actual zone areas
        
        return {
            "total_area": total_area,
            "average_rate": total_rate / len(rate_map) if rate_map else 0,
            "total_quantity": total_rate * total_area,
            "zone_breakdown": rate_map
        }
    
    def _get_application_timing(self, app_type: str, crop: str) -> Dict:
        """Get optimal application timing"""
        timing_recommendations = {
            "fertilizer": {
                "corn": {"pre_plant": "2-3 weeks before planting", "side_dress": "V6-V8 growth stage"},
                "soybean": {"pre_plant": "1-2 weeks before planting"},
                "wheat": {"fall": "at planting", "spring": "early spring growth"}
            },
            "pesticide": {
                "corn": {"pre_emerge": "within 3 days of planting", "post_emerge": "V3-V6 stage"},
                "soybean": {"pre_emerge": "within 2 days of planting", "post_emerge": "V2-V4 stage"},
                "wheat": {"fall": "4-6 weeks after emergence", "spring": "early spring"}
            }
        }
        
        return timing_recommendations.get(app_type, {}).get(crop, {"general": "consult agronomist"})
    
    def _recommend_equipment(self, app_type: str, field_size: float) -> Dict:
        """Recommend equipment for application"""
        equipment_recommendations = {
            "fertilizer": {
                "small": "Broadcast spreader with GPS guidance",
                "medium": "Self-propelled applicator with variable rate",
                "large": "High-capacity applicator with precision guidance"
            },
            "pesticide": {
                "small": "ATV-mounted sprayer",
                "medium": "Self-propelled sprayer with boom",
                "large": "High-clearance sprayer with GPS"
            },
            "seed": {
                "small": "Precision planter",
                "medium": "Multi-row planter with GPS",
                "large": "Large planter with variable rate seeding"
            }
        }
        
        size_category = "small" if field_size < 20 else "medium" if field_size < 100 else "large"
        
        return {
            "recommended_equipment": equipment_recommendations.get(app_type, {}).get(size_category, "Standard equipment"),
            "features_needed": ["GPS guidance", "variable rate capability", "application mapping"],
            "calibration_notes": "Calibrate equipment before each use for accuracy"
        }
    
    def _calculate_application_cost(self, quantities: Dict, app_type: str) -> Dict:
        """Calculate application costs"""
        cost_per_unit = {
            "fertilizer": 0.50,  # per kg
            "pesticide": 15.00,  # per liter
            "seed": 0.003,       # per seed
            "water": 0.10        # per mm
        }
        
        unit_cost = cost_per_unit.get(app_type, 1.0)
        total_quantity = quantities.get("total_quantity", 0)
        
        return {
            "product_cost": total_quantity * unit_cost,
            "application_cost": quantities.get("total_area", 0) * 25,  # $25/hectare
            "total_cost": (total_quantity * unit_cost) + (quantities.get("total_area", 0) * 25),
            "cost_per_hectare": ((total_quantity * unit_cost) + (quantities.get("total_area", 0) * 25)) / max(quantities.get("total_area", 1), 1)
        }
    
    def _generate_optimization_notes(self, rate_map: List[Dict]) -> List[str]:
        """Generate optimization notes for application"""
        notes = []
        
        rates = [zone.get("application_rate", 0) for zone in rate_map]
        if rates:
            rate_variance = np.var(rates)
            if rate_variance > 100:
                notes.append("High rate variability detected - ensure equipment calibration")
            
            max_rate = max(rates)
            min_rate = min(rates)
            if max_rate / min_rate > 2:
                notes.append("Consider splitting application into multiple passes")
        
        notes.extend([
            "Monitor weather conditions before application",
            "Ensure proper equipment calibration",
            "Document actual application rates for future reference",
            "Consider soil moisture conditions before application"
        ])
        
        return notes
    
    async def _analyze_ndvi_data(self, data_points: List, boundaries: List) -> Dict:
        """Analyze NDVI monitoring data"""
        if not data_points:
            return {"status": "no_data"}
        
        ndvi_values = [point.get("value", 0) for point in data_points]
        
        # Classify NDVI values
        poor_areas = len([v for v in ndvi_values if v < self.ndvi_thresholds["poor"]])
        fair_areas = len([v for v in ndvi_values if self.ndvi_thresholds["poor"] <= v < self.ndvi_thresholds["fair"]])
        good_areas = len([v for v in ndvi_values if self.ndvi_thresholds["fair"] <= v < self.ndvi_thresholds["good"]])
        excellent_areas = len([v for v in ndvi_values if v >= self.ndvi_thresholds["good"]])
        
        return {
            "average_ndvi": sum(ndvi_values) / len(ndvi_values),
            "ndvi_distribution": {
                "poor": poor_areas,
                "fair": fair_areas,
                "good": good_areas,
                "excellent": excellent_areas
            },
            "field_health_score": self._calculate_health_score(ndvi_values),
            "stress_indicators": self._identify_stress_areas(data_points),
            "growth_uniformity": self._assess_growth_uniformity(ndvi_values)
        }
    
    async def _analyze_soil_moisture_data(self, data_points: List, boundaries: List) -> Dict:
        """Analyze soil moisture monitoring data"""
        if not data_points:
            return {"status": "no_data"}
        
        moisture_values = [point.get("value", 0) for point in data_points]
        
        return {
            "average_moisture": sum(moisture_values) / len(moisture_values),
            "moisture_variability": np.var(moisture_values),
            "dry_areas": len([v for v in moisture_values if v < 20]),
            "optimal_areas": len([v for v in moisture_values if 20 <= v <= 80]),
            "wet_areas": len([v for v in moisture_values if v > 80]),
            "irrigation_recommendations": self._generate_irrigation_recommendations(moisture_values)
        }
    
    async def _analyze_temperature_data(self, data_points: List, boundaries: List) -> Dict:
        """Analyze temperature monitoring data"""
        if not data_points:
            return {"status": "no_data"}
        
        temp_values = [point.get("value", 0) for point in data_points]
        
        return {
            "average_temperature": sum(temp_values) / len(temp_values),
            "temperature_range": max(temp_values) - min(temp_values),
            "heat_stress_areas": len([v for v in temp_values if v > 35]),
            "cold_stress_areas": len([v for v in temp_values if v < 10]),
            "optimal_areas": len([v for v in temp_values if 15 <= v <= 30]),
            "thermal_recommendations": self._generate_thermal_recommendations(temp_values)
        }
    
    async def _analyze_growth_stage_data(self, data_points: List, boundaries: List) -> Dict:
        """Analyze crop growth stage data"""
        if not data_points:
            return {"status": "no_data"}
        
        stages = [point.get("value", 0) for point in data_points]
        
        return {
            "average_growth_stage": sum(stages) / len(stages),
            "growth_uniformity": np.std(stages),
            "advanced_areas": len([s for s in stages if s > np.mean(stages) + np.std(stages)]),
            "delayed_areas": len([s for s in stages if s < np.mean(stages) - np.std(stages)]),
            "management_recommendations": self._generate_growth_stage_recommendations(stages)
        }
    
    async def _analyze_generic_data(self, data_points: List, boundaries: List) -> Dict:
        """Analyze generic monitoring data"""
        if not data_points:
            return {"status": "no_data"}
        
        values = [point.get("value", 0) for point in data_points]
        
        return {
            "average_value": sum(values) / len(values),
            "min_value": min(values),
            "max_value": max(values),
            "standard_deviation": np.std(values),
            "data_quality": "good" if len(values) > 10 else "limited"
        }
    
    def _detect_field_anomalies(self, data_points: List, data_type: str) -> List[Dict]:
        """Detect anomalies in field data"""
        if not data_points:
            return []
        
        values = [point.get("value", 0) for point in data_points]
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        anomalies = []
        for i, point in enumerate(data_points):
            value = point.get("value", 0)
            if abs(value - mean_val) > 2 * std_val:  # 2 standard deviations
                anomalies.append({
                    "location": point.get("location", [0, 0]),
                    "value": value,
                    "expected_range": [mean_val - std_val, mean_val + std_val],
                    "severity": "high" if abs(value - mean_val) > 3 * std_val else "medium",
                    "type": "outlier"
                })
        
        return anomalies
    
    def _generate_monitoring_recommendations(self, analysis: Dict, anomalies: List, 
                                           data_type: str) -> List[str]:
        """Generate recommendations based on monitoring analysis"""
        recommendations = []
        
        if data_type == "ndvi":
            if analysis.get("field_health_score", 0) < 70:
                recommendations.append("Field health below optimal - investigate stress factors")
            if len(anomalies) > 0:
                recommendations.append("Address anomalous areas with targeted interventions")
        
        elif data_type == "soil_moisture":
            dry_areas = analysis.get("dry_areas", 0)
            if dry_areas > 0:
                recommendations.append("Increase irrigation in dry areas")
            wet_areas = analysis.get("wet_areas", 0)
            if wet_areas > 0:
                recommendations.append("Improve drainage in waterlogged areas")
        
        elif data_type == "temperature":
            heat_stress = analysis.get("heat_stress_areas", 0)
            if heat_stress > 0:
                recommendations.append("Implement heat stress mitigation strategies")
        
        recommendations.extend([
            "Continue regular monitoring for trend analysis",
            "Document any management interventions",
            "Compare with historical data for context"
        ])
        
        return recommendations
    
    def _calculate_field_statistics(self, data_points: List) -> Dict:
        """Calculate statistical summary of field data"""
        if not data_points:
            return {}
        
        values = [point.get("value", 0) for point in data_points]
        
        return {
            "count": len(values),
            "mean": np.mean(values),
            "median": np.median(values),
            "std_dev": np.std(values),
            "min": min(values),
            "max": max(values),
            "range": max(values) - min(values),
            "coefficient_of_variation": np.std(values) / np.mean(values) if np.mean(values) != 0 else 0
        }
    
    def _identify_spatial_patterns(self, data_points: List) -> Dict:
        """Identify spatial patterns in field data"""
        if len(data_points) < 4:
            return {"status": "insufficient_data"}
        
        # Simple spatial pattern analysis
        locations = [point.get("location", [0, 0]) for point in data_points]
        values = [point.get("value", 0) for point in data_points]
        
        # Check for north-south gradient
        north_values = [values[i] for i, loc in enumerate(locations) if loc[0] > np.mean([l[0] for l in locations])]
        south_values = [values[i] for i, loc in enumerate(locations) if loc[0] <= np.mean([l[0] for l in locations])]
        
        # Check for east-west gradient
        east_values = [values[i] for i, loc in enumerate(locations) if loc[1] > np.mean([l[1] for l in locations])]
        west_values = [values[i] for i, loc in enumerate(locations) if loc[1] <= np.mean([l[1] for l in locations])]
        
        patterns = {}
        
        if north_values and south_values:
            ns_diff = abs(np.mean(north_values) - np.mean(south_values))
            if ns_diff > np.std(values):
                patterns["north_south_gradient"] = {
                    "detected": True,
                    "direction": "north_higher" if np.mean(north_values) > np.mean(south_values) else "south_higher",
                    "magnitude": ns_diff
                }
        
        if east_values and west_values:
            ew_diff = abs(np.mean(east_values) - np.mean(west_values))
            if ew_diff > np.std(values):
                patterns["east_west_gradient"] = {
                    "detected": True,
                    "direction": "east_higher" if np.mean(east_values) > np.mean(west_values) else "west_higher",
                    "magnitude": ew_diff
                }
        
        return patterns
    
    def _suggest_next_monitoring_date(self, data_type: str) -> str:
        """Suggest next monitoring date based on data type"""
        intervals = {
            "ndvi": 14,  # Every 2 weeks
            "soil_moisture": 7,  # Weekly
            "temperature": 3,  # Every 3 days
            "growth_stage": 10  # Every 10 days
        }
        
        days_ahead = intervals.get(data_type, 7)
        next_date = datetime.utcnow() + timedelta(days=days_ahead)
        return next_date.isoformat()
    
    # Helper methods for various calculations
    def _identify_low_areas(self, elevation_data: List) -> List[Dict]:
        """Identify low-lying areas prone to water accumulation"""
        if not elevation_data:
            return []
        
        elevations = [point.get("elevation", 0) for point in elevation_data]
        threshold = np.percentile(elevations, 25)  # Bottom 25%
        
        low_areas = []
        for point in elevation_data:
            if point.get("elevation", 0) <= threshold:
                low_areas.append({
                    "location": point.get("location", [0, 0]),
                    "elevation": point.get("elevation", 0),
                    "risk_level": "high" if point.get("elevation", 0) <= np.percentile(elevations, 10) else "medium"
                })
        
        return low_areas
    
    def _identify_steep_areas(self, elevation_data: List) -> List[Dict]:
        """Identify steep areas prone to erosion"""
        if not elevation_data:
            return []
        
        elevations = [point.get("elevation", 0) for point in elevation_data]
        threshold = np.percentile(elevations, 75)  # Top 25%
        
        steep_areas = []
        for point in elevation_data:
            if point.get("elevation", 0) >= threshold:
                steep_areas.append({
                    "location": point.get("location", [0, 0]),
                    "elevation": point.get("elevation", 0),
                    "erosion_risk": "high" if point.get("elevation", 0) >= np.percentile(elevations, 90) else "medium"
                })
        
        return steep_areas
    
    def _get_soil_management_recommendations(self, soil_sample: Dict) -> List[str]:
        """Get soil-specific management recommendations"""
        recommendations = []
        
        ph = soil_sample.get("ph", 6.5)
        if ph < 6.0:
            recommendations.append("Apply lime to raise pH")
        elif ph > 7.5:
            recommendations.append("Apply sulfur to lower pH")
        
        organic_matter = soil_sample.get("organic_matter", 3.0)
        if organic_matter < 2.0:
            recommendations.append("Increase organic matter with cover crops or compost")
        
        nitrogen = soil_sample.get("nitrogen", 20)
        if nitrogen < 15:
            recommendations.append("Apply nitrogen fertilizer")
        
        return recommendations
    
    def _get_application_unit(self, app_type: str) -> str:
        """Get the appropriate unit for application type"""
        units = {
            "fertilizer": "kg/ha",
            "pesticide": "L/ha",
            "seed": "seeds/ha",
            "water": "mm"
        }
        return units.get(app_type, "units/ha")
    
    def _get_rate_justification(self, zone: Dict, rate_modifier: float) -> str:
        """Get justification for application rate"""
        if rate_modifier > 1.0:
            return f"Increased rate due to {', '.join(zone.get('characteristics', []))}"
        elif rate_modifier < 1.0:
            return f"Reduced rate due to {', '.join(zone.get('characteristics', []))}"
        else:
            return "Standard rate for zone conditions"
    
    def _calculate_health_score(self, ndvi_values: List[float]) -> float:
        """Calculate overall field health score from NDVI values"""
        if not ndvi_values:
            return 0.0
        
        avg_ndvi = sum(ndvi_values) / len(ndvi_values)
        # Convert NDVI (0-1) to health score (0-100)
        return min(100, avg_ndvi * 125)  # Scale factor to make 0.8 NDVI = 100% health
    
    def _identify_stress_areas(self, data_points: List) -> List[Dict]:
        """Identify areas showing stress indicators"""
        stress_areas = []
        
        for point in data_points:
            ndvi = point.get("value", 0)
            if ndvi < self.ndvi_thresholds["poor"]:
                stress_areas.append({
                    "location": point.get("location", [0, 0]),
                    "ndvi_value": ndvi,
                    "stress_level": "severe" if ndvi < 0.2 else "moderate",
                    "possible_causes": ["drought", "disease", "nutrient_deficiency", "pest_damage"]
                })
        
        return stress_areas
    
    def _assess_growth_uniformity(self, ndvi_values: List[float]) -> Dict:
        """Assess growth uniformity across the field"""
        if not ndvi_values:
            return {"status": "no_data"}
        
        std_dev = np.std(ndvi_values)
        cv = std_dev / np.mean(ndvi_values) if np.mean(ndvi_values) > 0 else 0
        
        uniformity_score = max(0, 100 - (cv * 100))  # Higher CV = lower uniformity
        
        return {
            "uniformity_score": uniformity_score,
            "coefficient_of_variation": cv,
            "assessment": "excellent" if uniformity_score > 80 else 
                         "good" if uniformity_score > 60 else
                         "fair" if uniformity_score > 40 else "poor",
            "recommendations": self._get_uniformity_recommendations(uniformity_score)
        }
    
    def _get_uniformity_recommendations(self, uniformity_score: float) -> List[str]:
        """Get recommendations based on growth uniformity"""
        if uniformity_score > 80:
            return ["Maintain current management practices", "Continue monitoring"]
        elif uniformity_score > 60:
            return ["Minor adjustments to management zones", "Monitor variable areas closely"]
        elif uniformity_score > 40:
            return ["Implement variable rate applications", "Investigate causes of variability"]
        else:
            return ["Major management zone revision needed", "Detailed soil and plant tissue testing", "Consider field renovation"]
    
    def _generate_irrigation_recommendations(self, moisture_values: List[float]) -> List[str]:
        """Generate irrigation recommendations based on soil moisture"""
        recommendations = []
        
        avg_moisture = sum(moisture_values) / len(moisture_values)
        
        if avg_moisture < 20:
            recommendations.append("Immediate irrigation required")
            recommendations.append("Increase irrigation frequency")
        elif avg_moisture < 40:
            recommendations.append("Schedule irrigation within 2-3 days")
        elif avg_moisture > 80:
            recommendations.append("Reduce irrigation frequency")
            recommendations.append("Check drainage systems")
        
        dry_areas = len([v for v in moisture_values if v < 20])
        if dry_areas > len(moisture_values) * 0.3:  # More than 30% of field is dry
            recommendations.append("Consider variable rate irrigation")
        
        return recommendations
    
    def _generate_thermal_recommendations(self, temp_values: List[float]) -> List[str]:
        """Generate recommendations based on temperature data"""
        recommendations = []
        
        avg_temp = sum(temp_values) / len(temp_values)
        heat_stress_areas = len([v for v in temp_values if v > 35])
        
        if avg_temp > 30:
            recommendations.append("Monitor for heat stress symptoms")
            recommendations.append("Ensure adequate irrigation")
        
        if heat_stress_areas > 0:
            recommendations.append("Implement heat stress mitigation in hot spots")
            recommendations.append("Consider shade structures or cooling systems")
        
        cold_areas = len([v for v in temp_values if v < 10])
        if cold_areas > 0:
            recommendations.append("Monitor for cold stress in low temperature areas")
            recommendations.append("Consider frost protection measures")
        
        return recommendations
    
    def _generate_growth_stage_recommendations(self, stages: List[float]) -> List[str]:
        """Generate recommendations based on growth stage analysis"""
        recommendations = []
        
        avg_stage = sum(stages) / len(stages)
        uniformity = np.std(stages)
        
        if uniformity > 1.0:  # High variability in growth stages
            recommendations.append("Address growth variability with targeted management")
            recommendations.append("Investigate causes of uneven development")
        
        advanced_areas = len([s for s in stages if s > avg_stage + uniformity])
        delayed_areas = len([s for s in stages if s < avg_stage - uniformity])
        
        if advanced_areas > 0:
            recommendations.append("Monitor advanced areas for early maturity")
        
        if delayed_areas > 0:
            recommendations.append("Provide additional support to delayed areas")
            recommendations.append("Consider supplemental fertilization in slow-growing zones")
        
        return recommendations
    
    async def _predict_zone_yield(self, zone: Dict, historical_yields: List, 
                                current_season: Dict, crop_type: str) -> Dict:
        """Predict yield for a specific management zone"""
        # Simplified yield prediction model
        base_yield = {
            "corn": 10000,  # kg/ha
            "soybean": 3000,
            "wheat": 5000
        }.get(crop_type, 5000)
        
        # Adjust based on zone characteristics
        yield_modifier = 1.0
        
        characteristics = zone.get("characteristics", [])
        if "good_drainage" in characteristics:
            yield_modifier *= 1.1
        elif "poor_drainage" in characteristics:
            yield_modifier *= 0.9
        
        if "high_organic_matter" in characteristics:
            yield_modifier *= 1.05
        
        # Weather impact
        weather_impact = current_season.get("weather_impact", 1.0)
        yield_modifier *= weather_impact
        
        predicted_yield = base_yield * yield_modifier
        
        # Calculate confidence based on historical data availability
        confidence = 0.7 if historical_yields else 0.5
        
        return {
            "zone_id": zone.get("zone_id", "unknown"),
            "predicted_yield_kg_ha": predicted_yield,
            "confidence": confidence,
            "yield_factors": {
                "base_yield": base_yield,
                "zone_modifier": yield_modifier,
                "weather_impact": weather_impact
            },
            "risk_factors": self._assess_zone_yield_risks(zone, current_season)
        }
    
    def _calculate_yield_statistics(self, yield_predictions: List[Dict]) -> Dict:
        """Calculate field-level yield statistics"""
        if not yield_predictions:
            return {}
        
        yields = [pred.get("predicted_yield_kg_ha", 0) for pred in yield_predictions]
        
        return {
            "average_yield_kg_ha": sum(yields) / len(yields),
            "min_yield_kg_ha": min(yields),
            "max_yield_kg_ha": max(yields),
            "yield_variability": np.std(yields),
            "total_zones": len(yield_predictions),
            "high_yield_zones": len([y for y in yields if y > np.mean(yields) + np.std(yields)]),
            "low_yield_zones": len([y for y in yields if y < np.mean(yields) - np.std(yields)])
        }
    
    def _create_yield_variability_map(self, yield_predictions: List[Dict]) -> Dict:
        """Create yield variability map"""
        if not yield_predictions:
            return {}
        
        yields = [pred.get("predicted_yield_kg_ha", 0) for pred in yield_predictions]
        mean_yield = np.mean(yields)
        std_yield = np.std(yields)
        
        variability_zones = []
        for pred in yield_predictions:
            yield_val = pred.get("predicted_yield_kg_ha", 0)
            deviation = (yield_val - mean_yield) / std_yield if std_yield > 0 else 0
            
            if deviation > 1:
                category = "high_yield"
            elif deviation > 0:
                category = "above_average"
            elif deviation > -1:
                category = "below_average"
            else:
                category = "low_yield"
            
            variability_zones.append({
                "zone_id": pred.get("zone_id"),
                "yield_category": category,
                "deviation_from_mean": deviation,
                "predicted_yield": yield_val
            })
        
        return {
            "zones": variability_zones,
            "field_mean": mean_yield,
            "field_std": std_yield,
            "variability_coefficient": std_yield / mean_yield if mean_yield > 0 else 0
        }
    
    def _assess_yield_risks(self, yield_predictions: List[Dict], current_season: Dict) -> Dict:
        """Assess risks to predicted yields"""
        risks = {
            "weather_risks": [],
            "pest_disease_risks": [],
            "management_risks": [],
            "market_risks": []
        }
        
        # Weather risks
        weather_conditions = current_season.get("weather_conditions", {})
        if weather_conditions.get("drought_risk", 0) > 0.5:
            risks["weather_risks"].append("High drought risk may reduce yields")
        
        if weather_conditions.get("excess_moisture", 0) > 0.5:
            risks["weather_risks"].append("Excess moisture may cause disease and reduce yields")
        
        # Yield variability risks
        yields = [pred.get("predicted_yield_kg_ha", 0) for pred in yield_predictions]
        if np.std(yields) / np.mean(yields) > 0.3:  # High coefficient of variation
            risks["management_risks"].append("High yield variability indicates management optimization opportunities")
        
        return risks
    
    def _calculate_prediction_confidence(self, historical_yields: List, current_season: Dict) -> float:
        """Calculate confidence level for yield predictions"""
        base_confidence = 0.6
        
        # Increase confidence with more historical data
        if len(historical_yields) > 3:
            base_confidence += 0.2
        elif len(historical_yields) > 1:
            base_confidence += 0.1
        
        # Adjust based on weather predictability
        weather_certainty = current_season.get("weather_certainty", 0.7)
        base_confidence *= weather_certainty
        
        return min(0.95, base_confidence)  # Cap at 95%
    
    def _assess_zone_yield_risks(self, zone: Dict, current_season: Dict) -> List[str]:
        """Assess yield risks for a specific zone"""
        risks = []
        
        characteristics = zone.get("characteristics", [])
        
        if "poor_drainage" in characteristics:
            risks.append("Waterlogging risk in wet conditions")
        
        if "low_organic_matter" in characteristics:
            risks.append("Nutrient deficiency risk")
        
        if "steep_slope" in characteristics:
            risks.append("Erosion risk during heavy rainfall")
        
        # Weather-related risks
        weather_risks = current_season.get("weather_risks", [])
        risks.extend(weather_risks)
        
        return risks