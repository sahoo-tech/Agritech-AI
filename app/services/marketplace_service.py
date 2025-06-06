"""
Marketplace Service
Connect farmers with suppliers and buyers
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import MarketplaceListing, User

logger = logging.getLogger(__name__)

class MarketplaceService:
    """Service for marketplace functionality"""
    
    def __init__(self):
        # Predefined categories for marketplace listings
        self.categories = {
            "seeds": {
                "display_name": "Seeds & Seedlings",
                "subcategories": ["Vegetable Seeds", "Grain Seeds", "Flower Seeds", "Seedlings"]
            },
            "fertilizers": {
                "display_name": "Fertilizers & Nutrients",
                "subcategories": ["Organic Fertilizers", "Chemical Fertilizers", "Micronutrients", "Soil Amendments"]
            },
            "pesticides": {
                "display_name": "Pesticides & Herbicides",
                "subcategories": ["Insecticides", "Fungicides", "Herbicides", "Organic Pest Control"]
            },
            "equipment": {
                "display_name": "Farm Equipment",
                "subcategories": ["Tractors", "Irrigation Systems", "Hand Tools", "Harvesting Equipment"]
            },
            "produce": {
                "display_name": "Fresh Produce",
                "subcategories": ["Vegetables", "Fruits", "Grains", "Herbs & Spices"]
            },
            "livestock": {
                "display_name": "Livestock & Poultry",
                "subcategories": ["Cattle", "Poultry", "Goats", "Feed & Supplements"]
            },
            "services": {
                "display_name": "Agricultural Services",
                "subcategories": ["Consulting", "Equipment Rental", "Transportation", "Processing"]
            }
        }
    
    async def create_listing(
        self,
        seller_id: int,
        listing_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a new marketplace listing"""
        try:
            # Validate required fields
            required_fields = ["listing_type", "title", "category", "price"]
            for field in required_fields:
                if field not in listing_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate category
            if listing_data["category"] not in self.categories:
                raise ValueError(f"Invalid category: {listing_data['category']}")
            
            # Create listing
            listing = MarketplaceListing(
                seller_id=seller_id,
                listing_type=listing_data["listing_type"],
                title=listing_data["title"],
                description=listing_data.get("description", ""),
                category=listing_data["category"],
                price=listing_data["price"],
                currency=listing_data.get("currency", "USD"),
                quantity_available=listing_data.get("quantity_available", 1),
                unit=listing_data.get("unit", "piece"),
                location=listing_data.get("location", ""),
                latitude=listing_data.get("latitude"),
                longitude=listing_data.get("longitude"),
                images=listing_data.get("images", []),
                contact_info=listing_data.get("contact_info", {}),
                expires_at=listing_data.get("expires_at")
            )
            
            db.add(listing)
            db.commit()
            db.refresh(listing)
            
            return {
                "success": True,
                "listing_id": listing.id,
                "message": "Listing created successfully",
                "listing": self._format_listing(listing)
            }
            
        except Exception as e:
            logger.error(f"Error creating listing: {str(e)}")
            db.rollback()
            raise
    
    async def search_listings(
        self,
        search_params: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Search marketplace listings"""
        try:
            query = db.query(MarketplaceListing).filter(
                MarketplaceListing.is_active == True
            )
            
            # Apply filters
            if search_params.get("category"):
                query = query.filter(MarketplaceListing.category == search_params["category"])
            
            if search_params.get("listing_type"):
                query = query.filter(MarketplaceListing.listing_type == search_params["listing_type"])
            
            if search_params.get("search_term"):
                search_term = f"%{search_params['search_term']}%"
                query = query.filter(
                    or_(
                        MarketplaceListing.title.ilike(search_term),
                        MarketplaceListing.description.ilike(search_term)
                    )
                )
            
            if search_params.get("min_price"):
                query = query.filter(MarketplaceListing.price >= search_params["min_price"])
            
            if search_params.get("max_price"):
                query = query.filter(MarketplaceListing.price <= search_params["max_price"])
            
            if search_params.get("location"):
                location_term = f"%{search_params['location']}%"
                query = query.filter(MarketplaceListing.location.ilike(location_term))
            
            # Location-based search (within radius)
            if search_params.get("latitude") and search_params.get("longitude"):
                # Simple distance filter (in a real implementation, use PostGIS or similar)
                lat = search_params["latitude"]
                lng = search_params["longitude"]
                radius = search_params.get("radius_km", 50)  # Default 50km radius
                
                # Approximate distance filter
                lat_range = radius / 111.0  # Rough conversion: 1 degree ≈ 111 km
                lng_range = radius / (111.0 * abs(lat))
                
                query = query.filter(
                    and_(
                        MarketplaceListing.latitude.between(lat - lat_range, lat + lat_range),
                        MarketplaceListing.longitude.between(lng - lng_range, lng + lng_range)
                    )
                )
            
            # Sorting
            sort_by = search_params.get("sort_by", "created_at")
            sort_order = search_params.get("sort_order", "desc")
            
            if sort_by == "price":
                if sort_order == "asc":
                    query = query.order_by(MarketplaceListing.price.asc())
                else:
                    query = query.order_by(MarketplaceListing.price.desc())
            elif sort_by == "created_at":
                if sort_order == "asc":
                    query = query.order_by(MarketplaceListing.created_at.asc())
                else:
                    query = query.order_by(MarketplaceListing.created_at.desc())
            
            # Pagination
            page = search_params.get("page", 1)
            per_page = min(search_params.get("per_page", 20), 100)  # Max 100 items per page
            offset = (page - 1) * per_page
            
            total_count = query.count()
            listings = query.offset(offset).limit(per_page).all()
            
            return {
                "success": True,
                "listings": [self._format_listing(listing) for listing in listings],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": (total_count + per_page - 1) // per_page
                },
                "filters_applied": search_params
            }
            
        except Exception as e:
            logger.error(f"Error searching listings: {str(e)}")
            raise
    
    async def get_listing_details(
        self,
        listing_id: int,
        db: Session = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific listing"""
        try:
            listing = db.query(MarketplaceListing).filter(
                MarketplaceListing.id == listing_id,
                MarketplaceListing.is_active == True
            ).first()
            
            if not listing:
                return None
            
            # Get seller information
            seller = db.query(User).filter(User.id == listing.seller_id).first()
            
            listing_data = self._format_listing(listing)
            listing_data["seller_info"] = {
                "name": seller.full_name if seller else "Unknown",
                "location": seller.location if seller else "",
                "member_since": seller.created_at.isoformat() if seller else ""
            }
            
            return listing_data
            
        except Exception as e:
            logger.error(f"Error getting listing details: {str(e)}")
            return None
    
    async def get_user_listings(
        self,
        user_id: int,
        include_inactive: bool = False,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get all listings for a specific user"""
        try:
            query = db.query(MarketplaceListing).filter(
                MarketplaceListing.seller_id == user_id
            )
            
            if not include_inactive:
                query = query.filter(MarketplaceListing.is_active == True)
            
            listings = query.order_by(MarketplaceListing.created_at.desc()).all()
            
            return [self._format_listing(listing) for listing in listings]
            
        except Exception as e:
            logger.error(f"Error getting user listings: {str(e)}")
            return []
    
    async def update_listing(
        self,
        listing_id: int,
        seller_id: int,
        update_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Update an existing listing"""
        try:
            listing = db.query(MarketplaceListing).filter(
                MarketplaceListing.id == listing_id,
                MarketplaceListing.seller_id == seller_id
            ).first()
            
            if not listing:
                return {
                    "success": False,
                    "message": "Listing not found or you don't have permission to edit it"
                }
            
            # Update allowed fields
            updatable_fields = [
                "title", "description", "price", "quantity_available", "unit",
                "location", "latitude", "longitude", "images", "contact_info",
                "is_active", "expires_at"
            ]
            
            for field in updatable_fields:
                if field in update_data:
                    setattr(listing, field, update_data[field])
            
            listing.updated_at = datetime.now()
            db.commit()
            
            return {
                "success": True,
                "message": "Listing updated successfully",
                "listing": self._format_listing(listing)
            }
            
        except Exception as e:
            logger.error(f"Error updating listing: {str(e)}")
            db.rollback()
            raise
    
    async def delete_listing(
        self,
        listing_id: int,
        seller_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Delete (deactivate) a listing"""
        try:
            listing = db.query(MarketplaceListing).filter(
                MarketplaceListing.id == listing_id,
                MarketplaceListing.seller_id == seller_id
            ).first()
            
            if not listing:
                return {
                    "success": False,
                    "message": "Listing not found or you don't have permission to delete it"
                }
            
            listing.is_active = False
            listing.updated_at = datetime.now()
            db.commit()
            
            return {
                "success": True,
                "message": "Listing deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Error deleting listing: {str(e)}")
            db.rollback()
            raise
    
    async def get_featured_listings(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """Get featured listings for homepage"""
        try:
            query = db.query(MarketplaceListing).filter(
                MarketplaceListing.is_active == True,
                MarketplaceListing.is_featured == True
            )
            
            if category:
                query = query.filter(MarketplaceListing.category == category)
            
            listings = query.order_by(MarketplaceListing.created_at.desc()).limit(limit).all()
            
            return [self._format_listing(listing) for listing in listings]
            
        except Exception as e:
            logger.error(f"Error getting featured listings: {str(e)}")
            return []
    
    async def get_marketplace_stats(self, db: Session = None) -> Dict[str, Any]:
        """Get marketplace statistics"""
        try:
            total_listings = db.query(MarketplaceListing).filter(
                MarketplaceListing.is_active == True
            ).count()
            
            # Count by category
            category_counts = {}
            for category in self.categories.keys():
                count = db.query(MarketplaceListing).filter(
                    MarketplaceListing.is_active == True,
                    MarketplaceListing.category == category
                ).count()
                category_counts[category] = count
            
            # Count by listing type
            type_counts = {}
            for listing_type in ["product", "service", "equipment"]:
                count = db.query(MarketplaceListing).filter(
                    MarketplaceListing.is_active == True,
                    MarketplaceListing.listing_type == listing_type
                ).count()
                type_counts[listing_type] = count
            
            # Recent listings (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_listings = db.query(MarketplaceListing).filter(
                MarketplaceListing.is_active == True,
                MarketplaceListing.created_at >= week_ago
            ).count()
            
            return {
                "total_active_listings": total_listings,
                "category_breakdown": category_counts,
                "type_breakdown": type_counts,
                "new_listings_this_week": recent_listings,
                "categories": self.categories
            }
            
        except Exception as e:
            logger.error(f"Error getting marketplace stats: {str(e)}")
            return {}
    
    def _format_listing(self, listing: MarketplaceListing) -> Dict[str, Any]:
        """Format listing data for API response"""
        return {
            "id": listing.id,
            "seller_id": listing.seller_id,
            "listing_type": listing.listing_type,
            "title": listing.title,
            "description": listing.description,
            "category": listing.category,
            "category_display": self.categories.get(listing.category, {}).get("display_name", listing.category),
            "price": listing.price,
            "currency": listing.currency,
            "quantity_available": listing.quantity_available,
            "unit": listing.unit,
            "location": listing.location,
            "latitude": listing.latitude,
            "longitude": listing.longitude,
            "images": listing.images or [],
            "contact_info": listing.contact_info or {},
            "is_active": listing.is_active,
            "is_featured": listing.is_featured,
            "expires_at": listing.expires_at.isoformat() if listing.expires_at else None,
            "created_at": listing.created_at.isoformat(),
            "updated_at": listing.updated_at.isoformat() if listing.updated_at else None
        }
    
    def get_categories(self) -> Dict[str, Any]:
        """Get all marketplace categories"""
        return self.categories
    
    def get_listing_types(self) -> List[Dict[str, str]]:
        """Get available listing types"""
        return [
            {"value": "product", "label": "Product"},
            {"value": "service", "label": "Service"},
            {"value": "equipment", "label": "Equipment"}
        ]
    
    async def generate_sample_listings(
        self,
        user_id: int,
        count: int = 10,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate sample listings for demonstration"""
        try:
            sample_listings = [
                {
                    "listing_type": "product",
                    "title": "Organic Tomato Seeds - High Yield Variety",
                    "description": "Premium organic tomato seeds with excellent disease resistance and high yield potential.",
                    "category": "seeds",
                    "price": 25.99,
                    "quantity_available": 100,
                    "unit": "packet",
                    "location": "California, USA"
                },
                {
                    "listing_type": "equipment",
                    "title": "John Deere Tractor - Model 5055E",
                    "description": "Well-maintained tractor with 500 hours. Perfect for medium-sized farms.",
                    "category": "equipment",
                    "price": 35000.00,
                    "quantity_available": 1,
                    "unit": "piece",
                    "location": "Iowa, USA"
                },
                {
                    "listing_type": "product",
                    "title": "Fresh Organic Carrots",
                    "description": "Freshly harvested organic carrots. Sweet and crunchy.",
                    "category": "produce",
                    "price": 3.50,
                    "quantity_available": 500,
                    "unit": "kg",
                    "location": "Vermont, USA"
                },
                {
                    "listing_type": "service",
                    "title": "Soil Testing and Analysis Service",
                    "description": "Professional soil testing with detailed nutrient analysis and recommendations.",
                    "category": "services",
                    "price": 75.00,
                    "quantity_available": 50,
                    "unit": "test",
                    "location": "Texas, USA"
                },
                {
                    "listing_type": "product",
                    "title": "Organic Compost - Premium Quality",
                    "description": "Rich organic compost made from farm waste. Perfect for improving soil health.",
                    "category": "fertilizers",
                    "price": 45.00,
                    "quantity_available": 200,
                    "unit": "bag",
                    "location": "Oregon, USA"
                }
            ]
            
            created_listings = []
            for i, listing_data in enumerate(sample_listings[:count]):
                listing = MarketplaceListing(
                    seller_id=user_id,
                    **listing_data
                )
                db.add(listing)
                created_listings.append(listing_data["title"])
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Created {len(created_listings)} sample listings",
                "listings": created_listings
            }
            
        except Exception as e:
            logger.error(f"Error generating sample listings: {str(e)}")
            db.rollback()
            raise