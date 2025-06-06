"""
Crop Yield Prediction API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ...core.database import get_db, CropYieldPrediction
from ...core.security import get_current_user
from ...services.crop_yield_service import CropYieldService

router = APIRouter(prefix="/crop-yield", tags=["Crop Yield Prediction"])

# Pydantic models
class CropYieldRequest(BaseModel):
    crop_type: str = Field(..., description="Type of crop to predict yield for")
    field_size_hectares: float = Field(..., gt=0, description="Field size in hectares")
    planting_date: datetime = Field(..., description="Planned or actual planting date")
    latitude: float = Field(..., ge=-90, le=90, description="Field latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Field longitude")
    soil_data: Optional[dict] = Field(None, description="Optional soil data")

class CropYieldResponse(BaseModel):
    success: bool
    prediction_id: Optional[int] = None
    crop_type: str
    predicted_yield_kg: float
    predicted_yield_per_hectare: float
    confidence_score: float
    recommendations: List[str]
    analysis_date: str

# Initialize service
crop_yield_service = CropYieldService()

@router.post("/predict", response_model=CropYieldResponse)
async def predict_crop_yield(
    request: CropYieldRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Predict crop yield based on various factors
    """
    try:
        # Get prediction from service
        prediction = await crop_yield_service.predict_crop_yield(
            crop_type=request.crop_type,
            field_size_hectares=request.field_size_hectares,
            planting_date=request.planting_date,
            latitude=request.latitude,
            longitude=request.longitude,
            soil_data=request.soil_data
        )
        
        # Save prediction to database
        db_prediction = CropYieldPrediction(
            user_id=current_user.id,
            crop_type=prediction["crop_type"],
            field_size_hectares=request.field_size_hectares,
            planting_date=request.planting_date,
            expected_harvest_date=datetime.fromisoformat(prediction["expected_harvest_date"]),
            predicted_yield_kg=prediction["predicted_yield_kg"],
            confidence_score=prediction["confidence_score"],
            weather_factors=prediction["weather_factors"],
            soil_factors=prediction["soil_factors"],
            latitude=request.latitude,
            longitude=request.longitude
        )
        
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        return CropYieldResponse(
            success=True,
            prediction_id=db_prediction.id,
            crop_type=prediction["crop_type"],
            predicted_yield_kg=prediction["predicted_yield_kg"],
            predicted_yield_per_hectare=prediction["predicted_yield_per_hectare"],
            confidence_score=prediction["confidence_score"],
            recommendations=prediction["recommendations"],
            analysis_date=prediction["analysis_date"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting crop yield: {str(e)}"
        )

@router.get("/history")
async def get_yield_history(
    crop_type: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get historical yield predictions for the user
    """
    try:
        history = await crop_yield_service.get_historical_yield_data(
            user_id=current_user.id,
            crop_type=crop_type,
            db=db
        )
        
        return {
            "success": True,
            "history": history,
            "total_predictions": len(history)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting yield history: {str(e)}"
        )

@router.get("/supported-crops")
async def get_supported_crops():
    """
    Get list of supported crops for yield prediction
    """
    try:
        crops = crop_yield_service.get_supported_crops()
        
        return {
            "success": True,
            "supported_crops": crops,
            "total_crops": len(crops)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting supported crops: {str(e)}"
        )

@router.get("/prediction/{prediction_id}")
async def get_prediction_details(
    prediction_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific prediction
    """
    try:
        prediction = db.query(CropYieldPrediction).filter(
            CropYieldPrediction.id == prediction_id,
            CropYieldPrediction.user_id == current_user.id
        ).first()
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prediction not found"
            )
        
        return {
            "success": True,
            "prediction": {
                "id": prediction.id,
                "crop_type": prediction.crop_type,
                "field_size_hectares": prediction.field_size_hectares,
                "planting_date": prediction.planting_date.isoformat(),
                "expected_harvest_date": prediction.expected_harvest_date.isoformat() if prediction.expected_harvest_date else None,
                "predicted_yield_kg": prediction.predicted_yield_kg,
                "confidence_score": prediction.confidence_score,
                "weather_factors": prediction.weather_factors,
                "soil_factors": prediction.soil_factors,
                "latitude": prediction.latitude,
                "longitude": prediction.longitude,
                "created_at": prediction.created_at.isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting prediction details: {str(e)}"
        )