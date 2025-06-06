"""
Marketplace API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.security import get_current_user
from ...services.marketplace_service import MarketplaceService

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])

# Pydantic models
class ListingCreate(BaseModel):
    listing_type: str = Field(..., description="Type of listing: product, service, or equipment")
    title: str = Field(..., min_length=5, max_length=200, description="Listing title")
    description: Optional[str] = Field(None, description="Detailed description")
    category: str = Field(..., description="Listing category")
    price: float = Field(..., ge=0, description="Price")
    currency: str = Field("USD", description="Currency code")
    quantity_available: int = Field(1, ge=1, description="Available quantity")
    unit: str = Field("piece", description="Unit of measurement")
    location: Optional[str] = Field(None, description="Location description")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    images: Optional[List[str]] = Field(None, description="Image URLs")
    contact_info: Optional[dict] = Field(None, description="Contact information")
    expires_at: Optional[datetime] = Field(None, description="Listing expiration date")

class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    quantity_available: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = None
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    images: Optional[List[str]] = None
    contact_info: Optional[dict] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None

class SearchFilters(BaseModel):
    search_term: Optional[str] = None
    category: Optional[str] = None
    listing_type: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    location: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    radius_km: Optional[float] = Field(50, ge=1, le=1000)
    sort_by: str = Field("created_at", description="Sort by: created_at, price")
    sort_order: str = Field("desc", description="Sort order: asc, desc")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=100)

# Initialize service
marketplace_service = MarketplaceService()

@router.post("/listings")
async def create_listing(
    listing_data: ListingCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new marketplace listing
    """
    try:
        result = await marketplace_service.create_listing(
            seller_id=current_user.id,
            listing_data=listing_data.dict(),
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating listing: {str(e)}"
        )

@router.get("/listings/search")
async def search_listings(
    search_term: Optional[str] = None,
    category: Optional[str] = None,
    listing_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: float = 50,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
):
    """
    Search marketplace listings
    """
    try:
        search_params = {
            "search_term": search_term,
            "category": category,
            "listing_type": listing_type,
            "min_price": min_price,
            "max_price": max_price,
            "location": location,
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "page": page,
            "per_page": per_page
        }
        
        result = await marketplace_service.search_listings(
            search_params=search_params,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching listings: {str(e)}"
        )

@router.get("/listings/{listing_id}")
async def get_listing_details(
    listing_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific listing
    """
    try:
        listing = await marketplace_service.get_listing_details(
            listing_id=listing_id,
            db=db
        )
        
        if not listing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Listing not found"
            )
        
        return {
            "success": True,
            "listing": listing
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting listing details: {str(e)}"
        )

@router.get("/listings/my")
async def get_my_listings(
    include_inactive: bool = False,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all listings for the current user
    """
    try:
        listings = await marketplace_service.get_user_listings(
            user_id=current_user.id,
            include_inactive=include_inactive,
            db=db
        )
        
        return {
            "success": True,
            "listings": listings,
            "total_listings": len(listings)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user listings: {str(e)}"
        )

@router.put("/listings/{listing_id}")
async def update_listing(
    listing_id: int,
    update_data: ListingUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing listing
    """
    try:
        # Filter out None values
        update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
        
        result = await marketplace_service.update_listing(
            listing_id=listing_id,
            seller_id=current_user.id,
            update_data=update_dict,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating listing: {str(e)}"
        )

@router.delete("/listings/{listing_id}")
async def delete_listing(
    listing_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete (deactivate) a listing
    """
    try:
        result = await marketplace_service.delete_listing(
            listing_id=listing_id,
            seller_id=current_user.id,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting listing: {str(e)}"
        )

@router.get("/listings/featured")
async def get_featured_listings(
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get featured listings for homepage
    """
    try:
        listings = await marketplace_service.get_featured_listings(
            category=category,
            limit=limit,
            db=db
        )
        
        return {
            "success": True,
            "featured_listings": listings,
            "total_featured": len(listings)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting featured listings: {str(e)}"
        )

@router.get("/categories")
async def get_categories():
    """
    Get all marketplace categories
    """
    try:
        categories = marketplace_service.get_categories()
        listing_types = marketplace_service.get_listing_types()
        
        return {
            "success": True,
            "categories": categories,
            "listing_types": listing_types
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting categories: {str(e)}"
        )

@router.get("/stats")
async def get_marketplace_stats(
    db: Session = Depends(get_db)
):
    """
    Get marketplace statistics
    """
    try:
        stats = await marketplace_service.get_marketplace_stats(db=db)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting marketplace stats: {str(e)}"
        )

@router.post("/generate-samples")
async def generate_sample_listings(
    count: int = Query(10, ge=1, le=20),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate sample listings for demonstration
    """
    try:
        result = await marketplace_service.generate_sample_listings(
            user_id=current_user.id,
            count=count,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sample listings: {str(e)}"
        )