"""
Offline Service API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.security import get_current_user
from ...services.offline_service import OfflineService

router = APIRouter(prefix="/offline", tags=["Offline Services"])

# Pydantic models
class OfflinePackageRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Location latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Location longitude")

class RecommendationRequest(BaseModel):
    crop_type: Optional[str] = Field(None, description="Crop type for specific recommendations")
    issue_type: Optional[str] = Field(None, description="Issue type: disease, pest, watering, etc.")

# Initialize service
offline_service = OfflineService()

@router.post("/prepare-package")
async def prepare_offline_package(
    request: OfflinePackageRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Prepare a comprehensive offline data package for the user's location
    """
    try:
        package = await offline_service.prepare_offline_package(
            user_id=current_user.id,
            latitude=request.latitude,
            longitude=request.longitude,
            db=db
        )
        
        return package
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error preparing offline package: {str(e)}"
        )

@router.get("/cached-data/{data_type}")
async def get_cached_data(
    data_type: str,
    data_key: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve specific cached data for offline use
    """
    try:
        cached_data = await offline_service.get_cached_data(
            user_id=current_user.id,
            data_type=data_type,
            data_key=data_key,
            db=db
        )
        
        if not cached_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No cached data found for type: {data_type}"
            )
        
        return {
            "success": True,
            "cached_data": cached_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cached data: {str(e)}"
        )

@router.post("/recommendations")
async def get_offline_recommendations(
    request: RecommendationRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get offline recommendations for farming issues
    """
    try:
        recommendations = await offline_service.get_offline_recommendations(
            user_id=current_user.id,
            crop_type=request.crop_type,
            issue_type=request.issue_type,
            db=db
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting offline recommendations: {str(e)}"
        )

@router.get("/cache-status")
async def get_cache_status(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of user's cached data
    """
    try:
        status_info = await offline_service.get_cache_status(
            user_id=current_user.id,
            db=db
        )
        
        return {
            "success": True,
            "cache_status": status_info
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting cache status: {str(e)}"
        )

@router.post("/cleanup-cache")
async def cleanup_expired_cache(
    db: Session = Depends(get_db)
):
    """
    Clean up expired cached data (admin function)
    """
    try:
        result = await offline_service.cleanup_expired_cache(db=db)
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up cache: {str(e)}"
        )

@router.get("/disease-tips")
async def get_disease_tips(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cached disease prevention and treatment tips
    """
    try:
        tips = await offline_service.get_cached_data(
            user_id=current_user.id,
            data_type="disease_tips",
            db=db
        )
        
        if not tips:
            # Return default tips if no cached data
            tips = {
                "content": offline_service.offline_templates["disease_tips"],
                "source": "default_template"
            }
        
        return {
            "success": True,
            "disease_tips": tips
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting disease tips: {str(e)}"
        )

@router.get("/crop-calendar")
async def get_crop_calendar(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cached crop calendar information
    """
    try:
        calendar = await offline_service.get_cached_data(
            user_id=current_user.id,
            data_type="crop_calendar",
            db=db
        )
        
        if not calendar:
            # Return default calendar if no cached data
            calendar = {
                "content": offline_service.offline_templates["crop_calendar"],
                "source": "default_template"
            }
        
        return {
            "success": True,
            "crop_calendar": calendar
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting crop calendar: {str(e)}"
        )

@router.get("/farming-tips")
async def get_farming_tips(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cached farming tips and best practices
    """
    try:
        tips = await offline_service.get_cached_data(
            user_id=current_user.id,
            data_type="farming_tips",
            db=db
        )
        
        if not tips:
            # Return default tips if no cached data
            tips = {
                "content": offline_service.offline_templates["farming_tips"],
                "source": "default_template"
            }
        
        return {
            "success": True,
            "farming_tips": tips
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting farming tips: {str(e)}"
        )

@router.get("/emergency-contacts")
async def get_emergency_contacts(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get cached emergency contacts and resources
    """
    try:
        contacts = await offline_service.get_cached_data(
            user_id=current_user.id,
            data_type="emergency_contacts",
            db=db
        )
        
        if not contacts:
            # Return default contacts if no cached data
            contacts = {
                "content": offline_service.offline_templates["emergency_contacts"],
                "source": "default_template"
            }
        
        return {
            "success": True,
            "emergency_contacts": contacts
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting emergency contacts: {str(e)}"
        )