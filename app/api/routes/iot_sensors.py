"""
IoT Sensor API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.security import get_current_user
from ...services.iot_service import IoTSensorService

router = APIRouter(prefix="/iot", tags=["IoT Sensors"])

# Pydantic models
class SensorRegistration(BaseModel):
    sensor_id: str = Field(..., description="Unique sensor identifier")
    sensor_type: str = Field(..., description="Type of sensor")
    location_name: str = Field(..., description="Human-readable location name")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Sensor latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Sensor longitude")
    metadata: Optional[dict] = Field(None, description="Additional sensor metadata")

class SensorDataInput(BaseModel):
    sensor_id: str = Field(..., description="Sensor identifier")
    value: float = Field(..., description="Sensor reading value")
    battery_level: Optional[float] = Field(None, ge=0, le=100, description="Battery level percentage")
    signal_strength: Optional[float] = Field(None, ge=0, le=100, description="Signal strength percentage")
    metadata: Optional[dict] = Field(None, description="Additional reading metadata")

class SensorDataQuery(BaseModel):
    sensor_id: Optional[str] = None
    sensor_type: Optional[str] = None
    hours: int = Field(24, ge=1, le=168, description="Hours of data to retrieve")

# Initialize service
iot_service = IoTSensorService()

@router.post("/sensors/register")
async def register_sensor(
    sensor_data: SensorRegistration,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Register a new IoT sensor
    """
    try:
        result = await iot_service.register_sensor(
            user_id=current_user.id,
            sensor_id=sensor_data.sensor_id,
            sensor_type=sensor_data.sensor_type,
            location_name=sensor_data.location_name,
            latitude=sensor_data.latitude,
            longitude=sensor_data.longitude,
            metadata=sensor_data.metadata,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering sensor: {str(e)}"
        )

@router.post("/sensors/data")
async def record_sensor_data(
    data: SensorDataInput,
    db: Session = Depends(get_db)
):
    """
    Record new sensor data reading
    Note: This endpoint doesn't require authentication for IoT devices
    """
    try:
        result = await iot_service.record_sensor_data(
            sensor_id=data.sensor_id,
            value=data.value,
            battery_level=data.battery_level,
            signal_strength=data.signal_strength,
            metadata=data.metadata,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording sensor data: {str(e)}"
        )

@router.get("/sensors/data")
async def get_sensor_data(
    sensor_id: Optional[str] = None,
    sensor_type: Optional[str] = None,
    hours: int = 24,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get sensor data for analysis
    """
    try:
        data = await iot_service.get_sensor_data(
            user_id=current_user.id,
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            hours=hours,
            db=db
        )
        
        return {
            "success": True,
            "sensor_data": data,
            "total_readings": len(data),
            "time_range_hours": hours
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sensor data: {str(e)}"
        )

@router.get("/sensors/summary")
async def get_sensor_summary(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get summary of all user's sensors
    """
    try:
        summary = await iot_service.get_sensor_summary(
            user_id=current_user.id,
            db=db
        )
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sensor summary: {str(e)}"
        )

@router.get("/sensors/types")
async def get_supported_sensor_types():
    """
    Get list of supported sensor types
    """
    try:
        sensor_types = iot_service.get_supported_sensors()
        
        return {
            "success": True,
            "supported_sensors": sensor_types,
            "total_types": len(sensor_types)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting sensor types: {str(e)}"
        )

@router.post("/sensors/simulate")
async def simulate_sensor_data(
    sensor_id: str,
    sensor_type: str,
    duration_hours: int = 24,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulate sensor data for demonstration purposes
    """
    try:
        simulation = await iot_service.simulate_sensor_data(
            user_id=current_user.id,
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            duration_hours=duration_hours,
            db=db
        )
        
        return simulation
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error simulating sensor data: {str(e)}"
        )