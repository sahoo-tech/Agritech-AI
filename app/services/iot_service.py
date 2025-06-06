"""
IoT Sensor Integration Service
Support for agricultural sensors and real-time monitoring
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
import random
import asyncio

from ..core.database import IoTSensorData, User

logger = logging.getLogger(__name__)

class IoTSensorService:
    """Service for IoT sensor data management and analysis"""
    
    def __init__(self):
        # Supported sensor types and their configurations
        self.sensor_types = {
            "soil_moisture": {
                "unit": "%",
                "min_value": 0,
                "max_value": 100,
                "optimal_range": (40, 70),
                "critical_low": 20,
                "critical_high": 90
            },
            "soil_temperature": {
                "unit": "°C",
                "min_value": -10,
                "max_value": 50,
                "optimal_range": (15, 25),
                "critical_low": 5,
                "critical_high": 35
            },
            "air_temperature": {
                "unit": "°C",
                "min_value": -20,
                "max_value": 60,
                "optimal_range": (18, 28),
                "critical_low": 0,
                "critical_high": 40
            },
            "air_humidity": {
                "unit": "%",
                "min_value": 0,
                "max_value": 100,
                "optimal_range": (60, 80),
                "critical_low": 30,
                "critical_high": 95
            },
            "light_intensity": {
                "unit": "lux",
                "min_value": 0,
                "max_value": 100000,
                "optimal_range": (20000, 50000),
                "critical_low": 5000,
                "critical_high": 80000
            },
            "ph_level": {
                "unit": "pH",
                "min_value": 0,
                "max_value": 14,
                "optimal_range": (6.0, 7.5),
                "critical_low": 4.5,
                "critical_high": 9.0
            },
            "nitrogen_level": {
                "unit": "ppm",
                "min_value": 0,
                "max_value": 1000,
                "optimal_range": (200, 400),
                "critical_low": 50,
                "critical_high": 600
            },
            "phosphorus_level": {
                "unit": "ppm",
                "min_value": 0,
                "max_value": 500,
                "optimal_range": (30, 80),
                "critical_low": 10,
                "critical_high": 150
            },
            "potassium_level": {
                "unit": "ppm",
                "min_value": 0,
                "max_value": 1000,
                "optimal_range": (150, 300),
                "critical_low": 50,
                "critical_high": 500
            }
        }
    
    async def register_sensor(
        self,
        user_id: int,
        sensor_id: str,
        sensor_type: str,
        location_name: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        metadata: Optional[Dict] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Register a new IoT sensor"""
        try:
            if sensor_type not in self.sensor_types:
                raise ValueError(f"Unsupported sensor type: {sensor_type}")
            
            # Check if sensor already exists
            existing_sensor = db.query(IoTSensorData).filter(
                IoTSensorData.sensor_id == sensor_id,
                IoTSensorData.user_id == user_id
            ).first()
            
            if existing_sensor:
                return {
                    "success": False,
                    "message": f"Sensor {sensor_id} already registered"
                }
            
            # Create initial sensor record
            sensor_data = IoTSensorData(
                user_id=user_id,
                sensor_id=sensor_id,
                sensor_type=sensor_type,
                location_name=location_name,
                latitude=latitude,
                longitude=longitude,
                value=0.0,  # Initial value
                unit=self.sensor_types[sensor_type]["unit"],
                battery_level=100.0,
                signal_strength=100.0,
                metadata=metadata or {}
            )
            
            db.add(sensor_data)
            db.commit()
            
            return {
                "success": True,
                "message": f"Sensor {sensor_id} registered successfully",
                "sensor_info": {
                    "sensor_id": sensor_id,
                    "sensor_type": sensor_type,
                    "location_name": location_name,
                    "unit": self.sensor_types[sensor_type]["unit"],
                    "optimal_range": self.sensor_types[sensor_type]["optimal_range"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error registering sensor: {str(e)}")
            db.rollback()
            raise
    
    async def record_sensor_data(
        self,
        sensor_id: str,
        value: float,
        battery_level: Optional[float] = None,
        signal_strength: Optional[float] = None,
        metadata: Optional[Dict] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Record new sensor data reading"""
        try:
            # Get sensor info
            sensor = db.query(IoTSensorData).filter(
                IoTSensorData.sensor_id == sensor_id
            ).order_by(IoTSensorData.timestamp.desc()).first()
            
            if not sensor:
                raise ValueError(f"Sensor {sensor_id} not found")
            
            # Validate value range
            sensor_config = self.sensor_types[sensor.sensor_type]
            if not (sensor_config["min_value"] <= value <= sensor_config["max_value"]):
                logger.warning(f"Sensor value {value} outside valid range for {sensor.sensor_type}")
            
            # Create new sensor data record
            new_data = IoTSensorData(
                user_id=sensor.user_id,
                sensor_id=sensor_id,
                sensor_type=sensor.sensor_type,
                location_name=sensor.location_name,
                latitude=sensor.latitude,
                longitude=sensor.longitude,
                value=value,
                unit=sensor.unit,
                battery_level=battery_level or sensor.battery_level,
                signal_strength=signal_strength or sensor.signal_strength,
                metadata=metadata or {}
            )
            
            db.add(new_data)
            db.commit()
            
            # Analyze the reading
            analysis = self._analyze_sensor_reading(sensor.sensor_type, value)
            
            return {
                "success": True,
                "sensor_id": sensor_id,
                "value": value,
                "unit": sensor.unit,
                "timestamp": new_data.timestamp.isoformat(),
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"Error recording sensor data: {str(e)}")
            db.rollback()
            raise
    
    async def get_sensor_data(
        self,
        user_id: int,
        sensor_id: Optional[str] = None,
        sensor_type: Optional[str] = None,
        hours: int = 24,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get sensor data for analysis"""
        try:
            # Calculate time range
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Build query
            query = db.query(IoTSensorData).filter(
                IoTSensorData.user_id == user_id,
                IoTSensorData.timestamp >= start_time
            )
            
            if sensor_id:
                query = query.filter(IoTSensorData.sensor_id == sensor_id)
            
            if sensor_type:
                query = query.filter(IoTSensorData.sensor_type == sensor_type)
            
            sensor_data = query.order_by(IoTSensorData.timestamp.desc()).all()
            
            return [
                {
                    "id": data.id,
                    "sensor_id": data.sensor_id,
                    "sensor_type": data.sensor_type,
                    "location_name": data.location_name,
                    "value": data.value,
                    "unit": data.unit,
                    "battery_level": data.battery_level,
                    "signal_strength": data.signal_strength,
                    "timestamp": data.timestamp.isoformat(),
                    "analysis": self._analyze_sensor_reading(data.sensor_type, data.value)
                }
                for data in sensor_data
            ]
            
        except Exception as e:
            logger.error(f"Error getting sensor data: {str(e)}")
            return []
    
    async def get_sensor_summary(
        self,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get summary of all user's sensors"""
        try:
            # Get latest data for each sensor
            latest_data = {}
            
            # Get all unique sensors for the user
            sensors = db.query(IoTSensorData.sensor_id, IoTSensorData.sensor_type).filter(
                IoTSensorData.user_id == user_id
            ).distinct().all()
            
            for sensor_id, sensor_type in sensors:
                latest = db.query(IoTSensorData).filter(
                    IoTSensorData.user_id == user_id,
                    IoTSensorData.sensor_id == sensor_id
                ).order_by(IoTSensorData.timestamp.desc()).first()
                
                if latest:
                    latest_data[sensor_id] = {
                        "sensor_type": latest.sensor_type,
                        "location_name": latest.location_name,
                        "value": latest.value,
                        "unit": latest.unit,
                        "battery_level": latest.battery_level,
                        "signal_strength": latest.signal_strength,
                        "timestamp": latest.timestamp.isoformat(),
                        "status": self._get_sensor_status(latest.sensor_type, latest.value),
                        "analysis": self._analyze_sensor_reading(latest.sensor_type, latest.value)
                    }
            
            # Generate overall farm health score
            health_score = self._calculate_farm_health_score(latest_data)
            
            # Generate alerts
            alerts = self._generate_sensor_alerts(latest_data)
            
            return {
                "total_sensors": len(latest_data),
                "active_sensors": len([s for s in latest_data.values() if s["signal_strength"] > 0]),
                "farm_health_score": health_score,
                "sensors": latest_data,
                "alerts": alerts,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting sensor summary: {str(e)}")
            return {}
    
    def _analyze_sensor_reading(self, sensor_type: str, value: float) -> Dict[str, Any]:
        """Analyze a sensor reading and provide insights"""
        if sensor_type not in self.sensor_types:
            return {"status": "unknown", "message": "Unknown sensor type"}
        
        config = self.sensor_types[sensor_type]
        optimal_min, optimal_max = config["optimal_range"]
        
        if optimal_min <= value <= optimal_max:
            status = "optimal"
            message = f"Value is within optimal range ({optimal_min}-{optimal_max} {config['unit']})"
        elif value < config["critical_low"]:
            status = "critical_low"
            message = f"Value is critically low (below {config['critical_low']} {config['unit']})"
        elif value > config["critical_high"]:
            status = "critical_high"
            message = f"Value is critically high (above {config['critical_high']} {config['unit']})"
        elif value < optimal_min:
            status = "low"
            message = f"Value is below optimal range ({optimal_min}-{optimal_max} {config['unit']})"
        else:
            status = "high"
            message = f"Value is above optimal range ({optimal_min}-{optimal_max} {config['unit']})"
        
        return {
            "status": status,
            "message": message,
            "optimal_range": config["optimal_range"],
            "recommendations": self._get_sensor_recommendations(sensor_type, status)
        }
    
    def _get_sensor_status(self, sensor_type: str, value: float) -> str:
        """Get simple status for sensor reading"""
        analysis = self._analyze_sensor_reading(sensor_type, value)
        return analysis["status"]
    
    def _get_sensor_recommendations(self, sensor_type: str, status: str) -> List[str]:
        """Get recommendations based on sensor type and status"""
        recommendations = []
        
        if sensor_type == "soil_moisture":
            if status in ["low", "critical_low"]:
                recommendations.extend([
                    "Increase irrigation frequency",
                    "Check irrigation system for blockages",
                    "Consider mulching to retain moisture"
                ])
            elif status in ["high", "critical_high"]:
                recommendations.extend([
                    "Reduce irrigation frequency",
                    "Improve drainage",
                    "Check for waterlogging"
                ])
        
        elif sensor_type == "soil_temperature":
            if status in ["low", "critical_low"]:
                recommendations.extend([
                    "Consider using row covers",
                    "Apply mulch for insulation",
                    "Delay planting if too cold"
                ])
            elif status in ["high", "critical_high"]:
                recommendations.extend([
                    "Increase irrigation to cool soil",
                    "Use shade cloth",
                    "Apply organic mulch"
                ])
        
        elif sensor_type == "ph_level":
            if status in ["low", "critical_low"]:
                recommendations.extend([
                    "Apply lime to raise pH",
                    "Add wood ash in small amounts",
                    "Test soil before major amendments"
                ])
            elif status in ["high", "critical_high"]:
                recommendations.extend([
                    "Apply sulfur to lower pH",
                    "Add organic matter",
                    "Use acidifying fertilizers"
                ])
        
        elif sensor_type in ["nitrogen_level", "phosphorus_level", "potassium_level"]:
            if status in ["low", "critical_low"]:
                recommendations.extend([
                    f"Apply {sensor_type.split('_')[0]} fertilizer",
                    "Consider organic amendments",
                    "Test soil for nutrient balance"
                ])
            elif status in ["high", "critical_high"]:
                recommendations.extend([
                    "Reduce fertilizer application",
                    "Increase watering to leach excess",
                    "Monitor for nutrient burn"
                ])
        
        return recommendations
    
    def _calculate_farm_health_score(self, sensor_data: Dict) -> float:
        """Calculate overall farm health score based on sensor readings"""
        if not sensor_data:
            return 0.0
        
        total_score = 0
        sensor_count = 0
        
        for sensor_id, data in sensor_data.items():
            status = data["analysis"]["status"]
            
            # Score based on status
            if status == "optimal":
                score = 100
            elif status in ["low", "high"]:
                score = 70
            elif status in ["critical_low", "critical_high"]:
                score = 30
            else:
                score = 50
            
            total_score += score
            sensor_count += 1
        
        return round(total_score / sensor_count, 1) if sensor_count > 0 else 0.0
    
    def _generate_sensor_alerts(self, sensor_data: Dict) -> List[Dict[str, Any]]:
        """Generate alerts based on sensor readings"""
        alerts = []
        
        for sensor_id, data in sensor_data.items():
            status = data["analysis"]["status"]
            
            if status in ["critical_low", "critical_high"]:
                alerts.append({
                    "type": "critical",
                    "sensor_id": sensor_id,
                    "sensor_type": data["sensor_type"],
                    "location": data["location_name"],
                    "message": data["analysis"]["message"],
                    "recommendations": data["analysis"]["recommendations"]
                })
            elif status in ["low", "high"]:
                alerts.append({
                    "type": "warning",
                    "sensor_id": sensor_id,
                    "sensor_type": data["sensor_type"],
                    "location": data["location_name"],
                    "message": data["analysis"]["message"],
                    "recommendations": data["analysis"]["recommendations"]
                })
            
            # Battery alerts
            if data["battery_level"] < 20:
                alerts.append({
                    "type": "maintenance",
                    "sensor_id": sensor_id,
                    "location": data["location_name"],
                    "message": f"Low battery: {data['battery_level']}%",
                    "recommendations": ["Replace or recharge sensor battery"]
                })
            
            # Signal strength alerts
            if data["signal_strength"] < 30:
                alerts.append({
                    "type": "maintenance",
                    "sensor_id": sensor_id,
                    "location": data["location_name"],
                    "message": f"Weak signal: {data['signal_strength']}%",
                    "recommendations": ["Check sensor connectivity", "Relocate sensor if needed"]
                })
        
        return alerts
    
    async def simulate_sensor_data(
        self,
        user_id: int,
        sensor_id: str,
        sensor_type: str,
        duration_hours: int = 24,
        db: Session = None
    ) -> Dict[str, Any]:
        """Simulate sensor data for demonstration purposes"""
        try:
            if sensor_type not in self.sensor_types:
                raise ValueError(f"Unsupported sensor type: {sensor_type}")
            
            config = self.sensor_types[sensor_type]
            optimal_min, optimal_max = config["optimal_range"]
            
            # Generate simulated data points
            data_points = []
            current_time = datetime.now()
            
            for i in range(duration_hours * 4):  # Every 15 minutes
                timestamp = current_time - timedelta(minutes=i * 15)
                
                # Generate realistic value around optimal range with some variation
                base_value = (optimal_min + optimal_max) / 2
                variation = (optimal_max - optimal_min) * 0.3
                value = base_value + random.uniform(-variation, variation)
                
                # Ensure value is within sensor limits
                value = max(config["min_value"], min(config["max_value"], value))
                
                # Simulate battery drain
                battery_level = max(20, 100 - (i * 0.1))
                
                # Simulate signal strength variation
                signal_strength = random.uniform(70, 100)
                
                data_points.append({
                    "timestamp": timestamp.isoformat(),
                    "value": round(value, 2),
                    "battery_level": round(battery_level, 1),
                    "signal_strength": round(signal_strength, 1)
                })
            
            return {
                "success": True,
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "unit": config["unit"],
                "data_points": data_points[::-1],  # Reverse to chronological order
                "summary": {
                    "min_value": min(point["value"] for point in data_points),
                    "max_value": max(point["value"] for point in data_points),
                    "avg_value": round(sum(point["value"] for point in data_points) / len(data_points), 2),
                    "optimal_range": config["optimal_range"]
                }
            }
            
        except Exception as e:
            logger.error(f"Error simulating sensor data: {str(e)}")
            raise
    
    def get_supported_sensors(self) -> List[Dict[str, Any]]:
        """Get list of supported sensor types"""
        return [
            {
                "type": sensor_type,
                "display_name": sensor_type.replace("_", " ").title(),
                "unit": config["unit"],
                "optimal_range": config["optimal_range"],
                "description": self._get_sensor_description(sensor_type)
            }
            for sensor_type, config in self.sensor_types.items()
        ]
    
    def _get_sensor_description(self, sensor_type: str) -> str:
        """Get description for sensor type"""
        descriptions = {
            "soil_moisture": "Measures soil water content for irrigation management",
            "soil_temperature": "Monitors soil temperature for optimal planting conditions",
            "air_temperature": "Tracks ambient temperature for crop growth monitoring",
            "air_humidity": "Measures air humidity for disease prevention",
            "light_intensity": "Monitors light levels for photosynthesis optimization",
            "ph_level": "Measures soil acidity/alkalinity for nutrient availability",
            "nitrogen_level": "Tracks nitrogen content for fertilizer management",
            "phosphorus_level": "Monitors phosphorus levels for root development",
            "potassium_level": "Measures potassium for overall plant health"
        }
        return descriptions.get(sensor_type, "Agricultural sensor for farm monitoring")