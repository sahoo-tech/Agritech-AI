"""
Community Forum API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...core.security import get_current_user
from ...services.community_service import CommunityService

router = APIRouter(prefix="/community", tags=["Community Forum"])

# Pydantic models
class PostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200, description="Post title")
    content: str = Field(..., min_length=10, description="Post content")
    category: str = Field(..., description="Post category")
    tags: Optional[List[str]] = Field(None, description="Post tags")
    images: Optional[List[str]] = Field(None, description="Image URLs")
    location: Optional[str] = Field(None, description="Location description")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")

class ReplyCreate(BaseModel):
    content: str = Field(..., min_length=5, description="Reply content")
    images: Optional[List[str]] = Field(None, description="Image URLs")
    is_solution: bool = Field(False, description="Mark as solution for questions")

class PostFilters(BaseModel):
    category: Optional[str] = None
    author_id: Optional[int] = None
    search_term: Optional[str] = None
    tags: Optional[List[str]] = None
    location: Optional[str] = None
    sort_by: str = Field("created_at", description="Sort by: created_at, likes, replies, views")
    exclude_pinned: bool = Field(False, description="Exclude pinned posts")
    page: int = Field(1, ge=1)
    per_page: int = Field(20, ge=1, le=50)

# Initialize service
community_service = CommunityService()

@router.post("/posts")
async def create_post(
    post_data: PostCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new community post
    """
    try:
        result = await community_service.create_post(
            author_id=current_user.id,
            post_data=post_data.dict(),
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating post: {str(e)}"
        )

@router.get("/posts")
async def get_posts(
    category: Optional[str] = None,
    author_id: Optional[int] = None,
    search_term: Optional[str] = None,
    tags: Optional[str] = None,  # Comma-separated tags
    location: Optional[str] = None,
    sort_by: str = "created_at",
    exclude_pinned: bool = False,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get community posts with filtering and pagination
    """
    try:
        # Parse tags if provided
        tag_list = tags.split(",") if tags else None
        
        filters = {
            "category": category,
            "author_id": author_id,
            "search_term": search_term,
            "tags": tag_list,
            "location": location,
            "sort_by": sort_by,
            "exclude_pinned": exclude_pinned,
            "page": page,
            "per_page": per_page
        }
        
        result = await community_service.get_posts(
            filters=filters,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting posts: {str(e)}"
        )

@router.get("/posts/{post_id}")
async def get_post_details(
    post_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific post
    """
    try:
        post = await community_service.get_post_details(
            post_id=post_id,
            user_id=current_user.id if current_user else None,
            db=db
        )
        
        if not post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Post not found"
            )
        
        return {
            "success": True,
            "post": post
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting post details: {str(e)}"
        )

@router.post("/posts/{post_id}/replies")
async def create_reply(
    post_id: int,
    reply_data: ReplyCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a reply to a post
    """
    try:
        result = await community_service.create_reply(
            post_id=post_id,
            author_id=current_user.id,
            reply_data=reply_data.dict(),
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating reply: {str(e)}"
        )

@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Like or unlike a post
    """
    try:
        result = await community_service.like_post(
            post_id=post_id,
            user_id=current_user.id,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error liking post: {str(e)}"
        )

@router.post("/replies/{reply_id}/like")
async def like_reply(
    reply_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Like or unlike a reply
    """
    try:
        result = await community_service.like_reply(
            reply_id=reply_id,
            user_id=current_user.id,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error liking reply: {str(e)}"
        )

@router.post("/replies/{reply_id}/mark-solution")
async def mark_solution(
    reply_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark a reply as the solution to a question
    """
    try:
        result = await community_service.mark_solution(
            reply_id=reply_id,
            post_author_id=current_user.id,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking solution: {str(e)}"
        )

@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user's community activity summary
    """
    try:
        activity = await community_service.get_user_activity(
            user_id=user_id,
            db=db
        )
        
        return {
            "success": True,
            "activity": activity
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user activity: {str(e)}"
        )

@router.get("/stats")
async def get_community_stats(
    db: Session = Depends(get_db)
):
    """
    Get overall community statistics
    """
    try:
        stats = await community_service.get_community_stats(db=db)
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting community stats: {str(e)}"
        )

@router.get("/categories")
async def get_categories():
    """
    Get all community categories and common tags
    """
    try:
        categories = community_service.get_categories()
        tags = community_service.get_common_tags()
        
        return {
            "success": True,
            "categories": categories,
            "common_tags": tags
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting categories: {str(e)}"
        )

@router.post("/generate-samples")
async def generate_sample_posts(
    count: int = Query(5, ge=1, le=10),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate sample posts for demonstration
    """
    try:
        result = await community_service.generate_sample_posts(
            user_id=current_user.id,
            count=count,
            db=db
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating sample posts: {str(e)}"
        )