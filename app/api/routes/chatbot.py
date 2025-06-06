"""
AI Chatbot API routes
"""

import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db, User, ChatSession, ChatMessage
from ...core.security import get_current_active_user
from ...services.ai_service import AIService

router = APIRouter()

# Initialize AI service
ai_service = AIService()

# Pydantic models
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: str = "en"
    context: Optional[dict] = None

class ChatResponse(BaseModel):
    message: str
    session_id: str
    language: str
    confidence: float
    timestamp: str
    source: Optional[str] = None

class ChatSessionResponse(BaseModel):
    id: int
    session_id: str
    language: str
    created_at: datetime
    updated_at: datetime
    message_count: int

class ChatMessageResponse(BaseModel):
    id: int
    message_type: str
    content: str
    created_at: datetime

class LanguageResponse(BaseModel):
    code: str
    name: str

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Send a message to the AI assistant"""
    
    try:
        # Get or create chat session
        session_id = chat_request.session_id
        if not session_id:
            session_id = str(uuid.uuid4())
            
            # Create new session
            chat_session = ChatSession(
                user_id=current_user.id,
                session_id=session_id,
                language=chat_request.language
            )
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
        else:
            # Get existing session
            chat_session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id,
                ChatSession.user_id == current_user.id
            ).first()
            
            if not chat_session:
                raise HTTPException(status_code=404, detail="Chat session not found")
        
        # Save user message
        user_message = ChatMessage(
            session_id=chat_session.id,
            message_type="user",
            content=chat_request.message
        )
        db.add(user_message)
        
        # Get AI response
        ai_response = await ai_service.get_ai_response(
            message=chat_request.message,
            user_id=str(current_user.id),
            session_id=session_id,
            language=chat_request.language,
            context=chat_request.context
        )
        
        # Save AI response
        assistant_message = ChatMessage(
            session_id=chat_session.id,
            message_type="assistant",
            content=ai_response["message"]
        )
        db.add(assistant_message)
        
        # Update session timestamp
        chat_session.updated_at = datetime.utcnow()
        
        db.commit()
        
        return ChatResponse(
            message=ai_response["message"],
            session_id=session_id,
            language=ai_response.get("language", chat_request.language),
            confidence=ai_response.get("confidence", 0.8),
            timestamp=ai_response.get("timestamp", datetime.utcnow().isoformat()),
            source=ai_response.get("source")
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_chat_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get user's chat sessions"""
    
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id
    ).order_by(
        ChatSession.updated_at.desc()
    ).offset(offset).limit(limit).all()
    
    result = []
    for session in sessions:
        message_count = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).count()
        
        result.append(ChatSessionResponse(
            id=session.id,
            session_id=session.session_id,
            language=session.language,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count
        ))
    
    return result

@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0
):
    """Get messages from a specific chat session"""
    
    # Verify session belongs to user
    chat_session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == chat_session.id
    ).order_by(
        ChatMessage.created_at.asc()
    ).offset(offset).limit(limit).all()
    
    return [
        ChatMessageResponse(
            id=message.id,
            message_type=message.message_type,
            content=message.content,
            created_at=message.created_at
        )
        for message in messages
    ]

@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a chat session and all its messages"""
    
    # Verify session belongs to user
    chat_session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Delete all messages in the session
    db.query(ChatMessage).filter(
        ChatMessage.session_id == chat_session.id
    ).delete()
    
    # Delete the session
    db.delete(chat_session)
    db.commit()
    
    return {"message": "Chat session deleted successfully"}

@router.get("/languages", response_model=List[LanguageResponse])
async def get_supported_languages(
    current_user: User = Depends(get_current_active_user)
):
    """Get list of supported languages"""
    
    languages = ai_service.get_supported_languages()
    
    return [
        LanguageResponse(code=code, name=name)
        for code, name in languages.items()
    ]

@router.get("/public/languages", response_model=List[LanguageResponse])
async def get_supported_languages_public():
    """Get list of supported languages (public access)"""
    
    # Basic language support for public access
    public_languages = {
        "en": "English",
        "es": "Spanish",
        "fr": "French"
    }
    
    return [
        LanguageResponse(code=code, name=name)
        for code, name in public_languages.items()
    ]

@router.post("/analyze-query")
async def analyze_query(
    query: str,
    current_user: User = Depends(get_current_active_user)
):
    """Analyze a farming query to extract intent and entities"""
    
    try:
        analysis = await ai_service.analyze_farming_query(query)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing query: {str(e)}")

@router.post("/crop-recommendations")
async def get_crop_recommendations(
    location: dict,
    season: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get crop recommendations based on location and season"""
    
    try:
        recommendations = await ai_service.get_crop_recommendations(location, season)
        return recommendations
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@router.post("/quick-advice")
async def get_quick_advice(
    topic: str,
    current_user: User = Depends(get_current_active_user)
):
    """Get quick advice on common farming topics"""
    
    try:
        # Create a temporary session for quick advice
        temp_session_id = f"quick_{uuid.uuid4()}"
        
        response = await ai_service.get_ai_response(
            message=f"Give me quick advice about {topic}",
            user_id=str(current_user.id),
            session_id=temp_session_id,
            language="en"
        )
        
        return {
            "topic": topic,
            "advice": response["message"],
            "confidence": response.get("confidence", 0.8)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting advice: {str(e)}")

@router.get("/conversation-starters")
async def get_conversation_starters(
    current_user: User = Depends(get_current_active_user)
):
    """Get suggested conversation starters for new users"""
    
    starters = [
        {
            "category": "Crop Management",
            "questions": [
                "What crops should I plant this season?",
                "How do I improve my soil quality?",
                "When is the best time to harvest tomatoes?"
            ]
        },
        {
            "category": "Disease & Pest Control",
            "questions": [
                "How do I identify plant diseases?",
                "What are natural pest control methods?",
                "My plants have yellow leaves, what's wrong?"
            ]
        },
        {
            "category": "Weather & Climate",
            "questions": [
                "How does weather affect my crops?",
                "Should I water my plants today?",
                "How to protect crops from frost?"
            ]
        },
        {
            "category": "Organic Farming",
            "questions": [
                "How do I start organic farming?",
                "What are the best organic fertilizers?",
                "How to make compost at home?"
            ]
        }
    ]
    
    return {"conversation_starters": starters}

@router.get("/public/conversation-starters")
async def get_conversation_starters_public():
    """Get suggested conversation starters for new users (public access)"""
    
    # Limited conversation starters for public access
    starters = [
        {
            "category": "Getting Started",
            "questions": [
                "What is this agricultural assistant?",
                "How can I analyze plant diseases?",
                "What weather information is available?"
            ]
        },
        {
            "category": "Basic Information",
            "questions": [
                "What crops can I grow in my area?",
                "How do I check soil conditions?",
                "What are common plant diseases?"
            ]
        }
    ]
    
    return {
        "conversation_starters": starters,
        "note": "For full AI assistance, please register and login."
    }

@router.post("/feedback")
async def submit_feedback(
    session_id: str,
    message_id: int,
    rating: int,  # 1-5 scale
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Submit feedback for AI responses"""
    
    # Verify the message belongs to the user
    chat_session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    message = db.query(ChatMessage).filter(
        ChatMessage.id == message_id,
        ChatMessage.session_id == chat_session.id
    ).first()
    
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    # In a real application, you would store this feedback in a separate table
    # For now, we'll just return a success response
    
    return {
        "message": "Feedback submitted successfully",
        "rating": rating,
        "feedback": feedback
    }