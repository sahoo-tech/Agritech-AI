"""
Community Service
Farmer forums and knowledge sharing platform
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..core.database import CommunityPost, CommunityReply, User

logger = logging.getLogger(__name__)

class CommunityService:
    """Service for community forum functionality"""
    
    def __init__(self):
        # Predefined categories for community posts
        self.categories = {
            "question": {
                "display_name": "Questions & Help",
                "description": "Ask questions and get help from the community",
                "icon": "❓"
            },
            "tip": {
                "display_name": "Tips & Tricks",
                "description": "Share your farming knowledge and tips",
                "icon": "💡"
            },
            "discussion": {
                "display_name": "General Discussion",
                "description": "General farming discussions and conversations",
                "icon": "💬"
            },
            "news": {
                "display_name": "News & Updates",
                "description": "Agricultural news and industry updates",
                "icon": "📰"
            },
            "showcase": {
                "display_name": "Farm Showcase",
                "description": "Show off your crops, equipment, and achievements",
                "icon": "🏆"
            },
            "market": {
                "display_name": "Market Talk",
                "description": "Discuss prices, trends, and market conditions",
                "icon": "📈"
            }
        }
        
        # Common tags for posts
        self.common_tags = [
            "organic", "irrigation", "pest-control", "fertilizer", "seeds",
            "harvest", "soil-health", "weather", "equipment", "livestock",
            "vegetables", "fruits", "grains", "greenhouse", "sustainable"
        ]
    
    async def create_post(
        self,
        author_id: int,
        post_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a new community post"""
        try:
            # Validate required fields
            required_fields = ["title", "content", "category"]
            for field in required_fields:
                if field not in post_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate category
            if post_data["category"] not in self.categories:
                raise ValueError(f"Invalid category: {post_data['category']}")
            
            # Create post
            post = CommunityPost(
                author_id=author_id,
                title=post_data["title"],
                content=post_data["content"],
                category=post_data["category"],
                tags=post_data.get("tags", []),
                images=post_data.get("images", []),
                location=post_data.get("location", ""),
                latitude=post_data.get("latitude"),
                longitude=post_data.get("longitude")
            )
            
            db.add(post)
            db.commit()
            db.refresh(post)
            
            return {
                "success": True,
                "post_id": post.id,
                "message": "Post created successfully",
                "post": self._format_post(post, db)
            }
            
        except Exception as e:
            logger.error(f"Error creating post: {str(e)}")
            db.rollback()
            raise
    
    async def get_posts(
        self,
        filters: Dict[str, Any] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get community posts with filtering and pagination"""
        try:
            filters = filters or {}
            
            query = db.query(CommunityPost)
            
            # Apply filters
            if filters.get("category"):
                query = query.filter(CommunityPost.category == filters["category"])
            
            if filters.get("author_id"):
                query = query.filter(CommunityPost.author_id == filters["author_id"])
            
            if filters.get("search_term"):
                search_term = f"%{filters['search_term']}%"
                query = query.filter(
                    or_(
                        CommunityPost.title.ilike(search_term),
                        CommunityPost.content.ilike(search_term)
                    )
                )
            
            if filters.get("tags"):
                # Filter by tags (simplified - in production, use proper JSON queries)
                for tag in filters["tags"]:
                    query = query.filter(CommunityPost.tags.contains([tag]))
            
            if filters.get("location"):
                location_term = f"%{filters['location']}%"
                query = query.filter(CommunityPost.location.ilike(location_term))
            
            # Sorting
            sort_by = filters.get("sort_by", "created_at")
            if sort_by == "likes":
                query = query.order_by(desc(CommunityPost.likes_count))
            elif sort_by == "replies":
                query = query.order_by(desc(CommunityPost.replies_count))
            elif sort_by == "views":
                query = query.order_by(desc(CommunityPost.views_count))
            else:
                query = query.order_by(desc(CommunityPost.created_at))
            
            # Handle pinned posts
            if not filters.get("exclude_pinned"):
                query = query.order_by(desc(CommunityPost.is_pinned), desc(CommunityPost.created_at))
            
            # Pagination
            page = filters.get("page", 1)
            per_page = min(filters.get("per_page", 20), 50)  # Max 50 posts per page
            offset = (page - 1) * per_page
            
            total_count = query.count()
            posts = query.offset(offset).limit(per_page).all()
            
            return {
                "success": True,
                "posts": [self._format_post(post, db) for post in posts],
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total_count": total_count,
                    "total_pages": (total_count + per_page - 1) // per_page
                },
                "filters_applied": filters
            }
            
        except Exception as e:
            logger.error(f"Error getting posts: {str(e)}")
            raise
    
    async def get_post_details(
        self,
        post_id: int,
        user_id: Optional[int] = None,
        db: Session = None
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific post"""
        try:
            post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
            
            if not post:
                return None
            
            # Increment view count
            post.views_count += 1
            db.commit()
            
            # Get replies
            replies = db.query(CommunityReply).filter(
                CommunityReply.post_id == post_id
            ).order_by(CommunityReply.created_at.asc()).all()
            
            post_data = self._format_post(post, db)
            post_data["replies"] = [self._format_reply(reply, db) for reply in replies]
            
            return post_data
            
        except Exception as e:
            logger.error(f"Error getting post details: {str(e)}")
            return None
    
    async def create_reply(
        self,
        post_id: int,
        author_id: int,
        reply_data: Dict[str, Any],
        db: Session = None
    ) -> Dict[str, Any]:
        """Create a reply to a post"""
        try:
            # Check if post exists
            post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
            if not post:
                return {
                    "success": False,
                    "message": "Post not found"
                }
            
            # Create reply
            reply = CommunityReply(
                post_id=post_id,
                author_id=author_id,
                content=reply_data["content"],
                images=reply_data.get("images", []),
                is_solution=reply_data.get("is_solution", False)
            )
            
            db.add(reply)
            
            # Update post reply count
            post.replies_count += 1
            
            # If this is marked as a solution, mark the post as solved
            if reply_data.get("is_solution") and post.category == "question":
                post.is_solved = True
            
            db.commit()
            db.refresh(reply)
            
            return {
                "success": True,
                "reply_id": reply.id,
                "message": "Reply created successfully",
                "reply": self._format_reply(reply, db)
            }
            
        except Exception as e:
            logger.error(f"Error creating reply: {str(e)}")
            db.rollback()
            raise
    
    async def like_post(
        self,
        post_id: int,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Like or unlike a post"""
        try:
            post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
            if not post:
                return {
                    "success": False,
                    "message": "Post not found"
                }
            
            # In a real implementation, you'd have a separate likes table
            # For now, just increment the counter
            post.likes_count += 1
            db.commit()
            
            return {
                "success": True,
                "message": "Post liked",
                "likes_count": post.likes_count
            }
            
        except Exception as e:
            logger.error(f"Error liking post: {str(e)}")
            db.rollback()
            raise
    
    async def like_reply(
        self,
        reply_id: int,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Like or unlike a reply"""
        try:
            reply = db.query(CommunityReply).filter(CommunityReply.id == reply_id).first()
            if not reply:
                return {
                    "success": False,
                    "message": "Reply not found"
                }
            
            # In a real implementation, you'd have a separate likes table
            # For now, just increment the counter
            reply.likes_count += 1
            db.commit()
            
            return {
                "success": True,
                "message": "Reply liked",
                "likes_count": reply.likes_count
            }
            
        except Exception as e:
            logger.error(f"Error liking reply: {str(e)}")
            db.rollback()
            raise
    
    async def mark_solution(
        self,
        reply_id: int,
        post_author_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Mark a reply as the solution to a question"""
        try:
            reply = db.query(CommunityReply).filter(CommunityReply.id == reply_id).first()
            if not reply:
                return {
                    "success": False,
                    "message": "Reply not found"
                }
            
            post = db.query(CommunityPost).filter(CommunityPost.id == reply.post_id).first()
            if not post:
                return {
                    "success": False,
                    "message": "Post not found"
                }
            
            # Only the post author can mark solutions
            if post.author_id != post_author_id:
                return {
                    "success": False,
                    "message": "Only the post author can mark solutions"
                }
            
            # Only questions can have solutions
            if post.category != "question":
                return {
                    "success": False,
                    "message": "Only questions can have solutions"
                }
            
            # Unmark any existing solutions
            db.query(CommunityReply).filter(
                CommunityReply.post_id == reply.post_id
            ).update({"is_solution": False})
            
            # Mark this reply as the solution
            reply.is_solution = True
            post.is_solved = True
            
            db.commit()
            
            return {
                "success": True,
                "message": "Reply marked as solution"
            }
            
        except Exception as e:
            logger.error(f"Error marking solution: {str(e)}")
            db.rollback()
            raise
    
    async def get_user_activity(
        self,
        user_id: int,
        db: Session = None
    ) -> Dict[str, Any]:
        """Get user's community activity summary"""
        try:
            # Get user's posts
            posts_count = db.query(CommunityPost).filter(
                CommunityPost.author_id == user_id
            ).count()
            
            # Get user's replies
            replies_count = db.query(CommunityReply).filter(
                CommunityReply.author_id == user_id
            ).count()
            
            # Get total likes received on posts
            posts_likes = db.query(CommunityPost).filter(
                CommunityPost.author_id == user_id
            ).all()
            total_post_likes = sum(post.likes_count for post in posts_likes)
            
            # Get total likes received on replies
            replies_likes = db.query(CommunityReply).filter(
                CommunityReply.author_id == user_id
            ).all()
            total_reply_likes = sum(reply.likes_count for reply in replies_likes)
            
            # Get solutions provided
            solutions_count = db.query(CommunityReply).filter(
                CommunityReply.author_id == user_id,
                CommunityReply.is_solution == True
            ).count()
            
            # Recent activity
            recent_posts = db.query(CommunityPost).filter(
                CommunityPost.author_id == user_id
            ).order_by(desc(CommunityPost.created_at)).limit(5).all()
            
            recent_replies = db.query(CommunityReply).filter(
                CommunityReply.author_id == user_id
            ).order_by(desc(CommunityReply.created_at)).limit(5).all()
            
            return {
                "user_id": user_id,
                "stats": {
                    "posts_count": posts_count,
                    "replies_count": replies_count,
                    "total_likes_received": total_post_likes + total_reply_likes,
                    "solutions_provided": solutions_count,
                    "reputation_score": self._calculate_reputation(
                        posts_count, replies_count, total_post_likes + total_reply_likes, solutions_count
                    )
                },
                "recent_posts": [self._format_post(post, db) for post in recent_posts],
                "recent_replies": [self._format_reply(reply, db) for reply in recent_replies]
            }
            
        except Exception as e:
            logger.error(f"Error getting user activity: {str(e)}")
            return {}
    
    async def get_community_stats(self, db: Session = None) -> Dict[str, Any]:
        """Get overall community statistics"""
        try:
            total_posts = db.query(CommunityPost).count()
            total_replies = db.query(CommunityReply).count()
            
            # Posts by category
            category_counts = {}
            for category in self.categories.keys():
                count = db.query(CommunityPost).filter(
                    CommunityPost.category == category
                ).count()
                category_counts[category] = count
            
            # Recent activity (last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            recent_posts = db.query(CommunityPost).filter(
                CommunityPost.created_at >= week_ago
            ).count()
            
            recent_replies = db.query(CommunityReply).filter(
                CommunityReply.created_at >= week_ago
            ).count()
            
            # Top contributors (users with most posts)
            # This would need a more complex query in production
            
            return {
                "total_posts": total_posts,
                "total_replies": total_replies,
                "category_breakdown": category_counts,
                "recent_activity": {
                    "posts_this_week": recent_posts,
                    "replies_this_week": recent_replies
                },
                "categories": self.categories
            }
            
        except Exception as e:
            logger.error(f"Error getting community stats: {str(e)}")
            return {}
    
    def _format_post(self, post: CommunityPost, db: Session) -> Dict[str, Any]:
        """Format post data for API response"""
        # Get author information
        author = db.query(User).filter(User.id == post.author_id).first()
        
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category": post.category,
            "category_info": self.categories.get(post.category, {}),
            "tags": post.tags or [],
            "images": post.images or [],
            "location": post.location,
            "latitude": post.latitude,
            "longitude": post.longitude,
            "likes_count": post.likes_count,
            "replies_count": post.replies_count,
            "views_count": post.views_count,
            "is_pinned": post.is_pinned,
            "is_solved": post.is_solved,
            "author": {
                "id": post.author_id,
                "name": author.full_name if author else "Unknown",
                "location": author.location if author else ""
            },
            "created_at": post.created_at.isoformat(),
            "updated_at": post.updated_at.isoformat() if post.updated_at else None
        }
    
    def _format_reply(self, reply: CommunityReply, db: Session) -> Dict[str, Any]:
        """Format reply data for API response"""
        # Get author information
        author = db.query(User).filter(User.id == reply.author_id).first()
        
        return {
            "id": reply.id,
            "post_id": reply.post_id,
            "content": reply.content,
            "images": reply.images or [],
            "likes_count": reply.likes_count,
            "is_solution": reply.is_solution,
            "author": {
                "id": reply.author_id,
                "name": author.full_name if author else "Unknown",
                "location": author.location if author else ""
            },
            "created_at": reply.created_at.isoformat(),
            "updated_at": reply.updated_at.isoformat() if reply.updated_at else None
        }
    
    def _calculate_reputation(
        self,
        posts_count: int,
        replies_count: int,
        likes_received: int,
        solutions_provided: int
    ) -> int:
        """Calculate user reputation score"""
        score = (
            posts_count * 5 +
            replies_count * 2 +
            likes_received * 1 +
            solutions_provided * 10
        )
        return score
    
    def get_categories(self) -> Dict[str, Any]:
        """Get all community categories"""
        return self.categories
    
    def get_common_tags(self) -> List[str]:
        """Get list of common tags"""
        return self.common_tags
    
    async def generate_sample_posts(
        self,
        user_id: int,
        count: int = 5,
        db: Session = None
    ) -> Dict[str, Any]:
        """Generate sample posts for demonstration"""
        try:
            sample_posts = [
                {
                    "title": "Best practices for organic pest control?",
                    "content": "I'm transitioning to organic farming and looking for effective pest control methods that don't harm beneficial insects. What has worked well for you?",
                    "category": "question",
                    "tags": ["organic", "pest-control", "sustainable"]
                },
                {
                    "title": "Amazing tomato harvest this season!",
                    "content": "Just wanted to share my excitement about this year's tomato crop. Used companion planting with basil and marigolds - the results speak for themselves!",
                    "category": "showcase",
                    "tags": ["tomatoes", "harvest", "companion-planting"]
                },
                {
                    "title": "Soil pH testing - DIY vs Professional",
                    "content": "What's your experience with DIY soil pH test kits versus professional soil testing? Is the extra cost worth it for small-scale farming?",
                    "category": "discussion",
                    "tags": ["soil-health", "testing", "ph"]
                },
                {
                    "title": "Water-saving irrigation tip",
                    "content": "Here's a simple tip that reduced my water usage by 30%: Install moisture sensors in different zones of your field. Only irrigate when soil moisture drops below optimal levels.",
                    "category": "tip",
                    "tags": ["irrigation", "water-conservation", "sensors"]
                },
                {
                    "title": "Market prices for organic vegetables trending up",
                    "content": "Noticed a significant increase in organic vegetable prices at local farmers markets. Great news for organic growers! Anyone else seeing similar trends?",
                    "category": "market",
                    "tags": ["organic", "prices", "market-trends"]
                }
            ]
            
            created_posts = []
            for i, post_data in enumerate(sample_posts[:count]):
                post = CommunityPost(
                    author_id=user_id,
                    **post_data
                )
                db.add(post)
                created_posts.append(post_data["title"])
            
            db.commit()
            
            return {
                "success": True,
                "message": f"Created {len(created_posts)} sample posts",
                "posts": created_posts
            }
            
        except Exception as e:
            logger.error(f"Error generating sample posts: {str(e)}")
            db.rollback()
            raise