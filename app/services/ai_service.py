"""
AI Service for multilingual agricultural assistance
Provides intelligent responses using OpenAI GPT and local language support
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import openai
from langdetect import detect
from googletrans import Translator
import re

from ..core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """Enhanced AI service for agricultural assistance"""
    
    def __init__(self):
        self.client = None
        self.translator = Translator()
        self.supported_languages = {
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'bn': 'Bengali',
            'ur': 'Urdu',
            'sw': 'Swahili',
            'am': 'Amharic',
            'yo': 'Yoruba',
            'ha': 'Hausa'
        }
        
        # Initialize OpenAI client if API key is available
        if settings.OPENAI_API_KEY:
            openai.api_key = settings.OPENAI_API_KEY
            self.client = openai
        
        # Agricultural knowledge base
        self.knowledge_base = self._load_agricultural_knowledge()
        
        # Conversation context storage
        self.conversation_contexts = {}
    
    def _load_agricultural_knowledge(self) -> Dict:
        """Load agricultural knowledge base"""
        return {
            "crops": {
                "tomato": {
                    "planting_season": "Spring to early summer",
                    "soil_requirements": "Well-drained, pH 6.0-6.8",
                    "water_needs": "Regular, deep watering",
                    "common_diseases": ["early_blight", "late_blight", "bacterial_spot"],
                    "harvest_time": "75-85 days from transplant"
                },
                "corn": {
                    "planting_season": "Late spring after soil warms",
                    "soil_requirements": "Rich, well-drained, pH 6.0-6.8",
                    "water_needs": "1-2 inches per week",
                    "common_diseases": ["corn_smut", "gray_leaf_spot"],
                    "harvest_time": "60-100 days depending on variety"
                },
                "wheat": {
                    "planting_season": "Fall for winter wheat, spring for spring wheat",
                    "soil_requirements": "Well-drained, pH 6.0-7.0",
                    "water_needs": "Moderate, drought tolerant when established",
                    "common_diseases": ["rust", "powdery_mildew"],
                    "harvest_time": "90-120 days"
                },
                "rice": {
                    "planting_season": "Varies by region, typically wet season",
                    "soil_requirements": "Clay or clay loam, flooded fields",
                    "water_needs": "Flooded conditions during growing season",
                    "common_diseases": ["blast", "bacterial_blight"],
                    "harvest_time": "100-150 days"
                }
            },
            "farming_practices": {
                "organic_farming": {
                    "description": "Farming without synthetic chemicals",
                    "benefits": ["Environmental protection", "Soil health", "Biodiversity"],
                    "challenges": ["Lower yields initially", "Higher labor costs", "Certification process"]
                },
                "precision_agriculture": {
                    "description": "Technology-driven farming approach",
                    "benefits": ["Optimized inputs", "Increased efficiency", "Data-driven decisions"],
                    "technologies": ["GPS", "Drones", "Sensors", "Variable rate application"]
                },
                "crop_rotation": {
                    "description": "Growing different crops in sequence",
                    "benefits": ["Soil fertility", "Pest control", "Disease prevention"],
                    "examples": ["Corn-Soybean", "Wheat-Fallow", "Vegetable rotations"]
                }
            },
            "pest_management": {
                "integrated_pest_management": {
                    "description": "Holistic approach to pest control",
                    "strategies": ["Biological control", "Cultural practices", "Chemical control as last resort"],
                    "monitoring": "Regular scouting and threshold-based decisions"
                },
                "biological_control": {
                    "description": "Using natural enemies to control pests",
                    "examples": ["Ladybugs for aphids", "Parasitic wasps", "Beneficial nematodes"],
                    "advantages": ["Environmentally friendly", "Sustainable", "Cost-effective long-term"]
                }
            },
            "soil_management": {
                "soil_testing": {
                    "importance": "Understanding soil nutrient status",
                    "frequency": "Every 2-3 years or before major plantings",
                    "parameters": ["pH", "Nutrients", "Organic matter", "Soil texture"]
                },
                "composting": {
                    "description": "Converting organic waste to soil amendment",
                    "benefits": ["Improves soil structure", "Adds nutrients", "Increases water retention"],
                    "materials": ["Kitchen scraps", "Yard waste", "Manure"]
                }
            }
        }
    
    async def get_ai_response(
        self, 
        message: str, 
        user_id: str, 
        session_id: str,
        language: str = "en",
        context: Optional[Dict] = None
    ) -> Dict:
        """Get AI response for user message"""
        try:
            # Detect language if not specified
            if language == "auto":
                language = await self._detect_language(message)
            
            # Translate to English if needed
            english_message = message
            if language != "en":
                english_message = await self._translate_text(message, "en")
            
            # Get conversation context
            conversation_context = self._get_conversation_context(session_id)
            
            # Generate response
            if self.client:
                response = await self._get_openai_response(
                    english_message, conversation_context, context
                )
            else:
                response = await self._get_fallback_response(
                    english_message, conversation_context, context
                )
            
            # Translate response back to user's language
            if language != "en":
                response["message"] = await self._translate_text(response["message"], language)
            
            # Update conversation context
            self._update_conversation_context(session_id, english_message, response["message"])
            
            # Add metadata
            response.update({
                "language": language,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "confidence": response.get("confidence", 0.8)
            })
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return {
                "message": "I apologize, but I'm having trouble processing your request right now. Please try again later.",
                "error": str(e),
                "language": language,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _get_openai_response(
        self, 
        message: str, 
        conversation_context: List[Dict],
        context: Optional[Dict] = None
    ) -> Dict:
        """Get response from OpenAI GPT"""
        try:
            # Build system prompt
            system_prompt = self._build_system_prompt(context)
            
            # Build conversation history
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation context
            for ctx in conversation_context[-5:]:  # Last 5 exchanges
                messages.append({"role": "user", "content": ctx["user"]})
                messages.append({"role": "assistant", "content": ctx["assistant"]})
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Get response from OpenAI
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7,
                    top_p=0.9
                )
            )
            
            ai_message = response.choices[0].message.content.strip()
            
            return {
                "message": ai_message,
                "confidence": 0.9,
                "source": "openai",
                "tokens_used": response.usage.total_tokens
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return await self._get_fallback_response(message, conversation_context, context)
    
    async def _get_fallback_response(
        self, 
        message: str, 
        conversation_context: List[Dict],
        context: Optional[Dict] = None
    ) -> Dict:
        """Get fallback response using rule-based system"""
        try:
            message_lower = message.lower()
            
            # Crop-specific questions
            for crop, info in self.knowledge_base["crops"].items():
                if crop in message_lower:
                    if any(word in message_lower for word in ["plant", "grow", "cultivation"]):
                        return {
                            "message": f"For {crop} cultivation: Plant during {info['planting_season']}. "
                                     f"Soil requirements: {info['soil_requirements']}. "
                                     f"Water needs: {info['water_needs']}. "
                                     f"Harvest time: {info['harvest_time']}.",
                            "confidence": 0.8,
                            "source": "knowledge_base"
                        }
                    elif any(word in message_lower for word in ["disease", "problem", "sick"]):
                        diseases = ", ".join(info["common_diseases"])
                        return {
                            "message": f"Common diseases affecting {crop} include: {diseases}. "
                                     f"For specific treatment recommendations, please provide more details about the symptoms you're observing.",
                            "confidence": 0.7,
                            "source": "knowledge_base"
                        }
            
            # Weather-related questions
            if any(word in message_lower for word in ["weather", "rain", "temperature", "climate"]):
                return {
                    "message": "Weather conditions significantly impact crop growth. Monitor temperature, humidity, and precipitation. "
                             "I can help you interpret weather data for your specific location if you provide your coordinates.",
                    "confidence": 0.7,
                    "source": "knowledge_base"
                }
            
            # Soil-related questions
            if any(word in message_lower for word in ["soil", "ph", "nutrients", "fertilizer"]):
                return {
                    "message": "Soil health is crucial for successful farming. Key factors include pH (6.0-7.0 for most crops), "
                             "nutrient levels (N-P-K), organic matter content, and drainage. "
                             "Regular soil testing every 2-3 years is recommended.",
                    "confidence": 0.8,
                    "source": "knowledge_base"
                }
            
            # Pest management questions
            if any(word in message_lower for word in ["pest", "insect", "bug", "control"]):
                return {
                    "message": "For effective pest management, I recommend Integrated Pest Management (IPM): "
                             "1) Regular monitoring, 2) Biological controls when possible, "
                             "3) Cultural practices like crop rotation, 4) Chemical controls as last resort. "
                             "Can you describe the specific pest problem you're facing?",
                    "confidence": 0.8,
                    "source": "knowledge_base"
                }
            
            # Organic farming questions
            if any(word in message_lower for word in ["organic", "natural", "chemical-free"]):
                organic_info = self.knowledge_base["farming_practices"]["organic_farming"]
                return {
                    "message": f"Organic farming involves {organic_info['description']}. "
                             f"Benefits include: {', '.join(organic_info['benefits'])}. "
                             f"Main challenges: {', '.join(organic_info['challenges'])}.",
                    "confidence": 0.8,
                    "source": "knowledge_base"
                }
            
            # General greeting or help
            if any(word in message_lower for word in ["hello", "hi", "help", "start"]):
                return {
                    "message": "Hello! I'm your AI agricultural assistant. I can help you with:\n"
                             "• Crop cultivation advice\n"
                             "• Disease and pest identification\n"
                             "• Soil and weather guidance\n"
                             "• Farming best practices\n"
                             "• Organic farming methods\n\n"
                             "What would you like to know about farming today?",
                    "confidence": 0.9,
                    "source": "knowledge_base"
                }
            
            # Default response
            return {
                "message": "I understand you're asking about farming. While I have knowledge about crops, "
                         "soil management, pest control, and weather impacts, I need more specific information "
                         "to provide the best advice. Could you please provide more details about your question?",
                "confidence": 0.6,
                "source": "knowledge_base"
            }
            
        except Exception as e:
            logger.error(f"Error in fallback response: {e}")
            return {
                "message": "I'm sorry, I'm having trouble understanding your question. "
                         "Could you please rephrase it or ask about a specific farming topic?",
                "confidence": 0.3,
                "source": "error_fallback"
            }
    
    def _build_system_prompt(self, context: Optional[Dict] = None) -> str:
        """Build system prompt for AI"""
        base_prompt = """You are an expert agricultural assistant with deep knowledge of farming practices, 
        crop management, soil science, pest control, and sustainable agriculture. You provide practical, 
        actionable advice to farmers and agricultural enthusiasts.

        Your responses should be:
        - Practical and actionable
        - Based on scientific agricultural principles
        - Considerate of sustainable farming practices
        - Clear and easy to understand
        - Culturally sensitive to different farming traditions

        You can help with:
        - Crop selection and cultivation
        - Disease and pest identification and treatment
        - Soil management and fertilization
        - Weather impact on farming
        - Organic and sustainable farming methods
        - Farm equipment and technology
        - Market and economic considerations

        Always ask for clarification if you need more specific information to provide better advice."""
        
        if context:
            if "location" in context:
                base_prompt += f"\n\nUser location context: {context['location']}"
            if "weather" in context:
                base_prompt += f"\n\nCurrent weather conditions: {context['weather']}"
            if "soil" in context:
                base_prompt += f"\n\nSoil conditions: {context['soil']}"
            if "crop_type" in context:
                base_prompt += f"\n\nUser is asking about: {context['crop_type']}"
        
        return base_prompt
    
    async def _detect_language(self, text: str) -> str:
        """Detect language of input text"""
        try:
            detected = detect(text)
            if detected in self.supported_languages:
                return detected
            return "en"  # Default to English
        except:
            return "en"
    
    async def _translate_text(self, text: str, target_language: str) -> str:
        """Translate text to target language"""
        try:
            if target_language == "en":
                # Translate to English
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.translator.translate, text, "en"
                )
                return result.text
            else:
                # Translate from English to target language
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self.translator.translate, text, target_language
                )
                return result.text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # Return original text if translation fails
    
    def _get_conversation_context(self, session_id: str) -> List[Dict]:
        """Get conversation context for session"""
        return self.conversation_contexts.get(session_id, [])
    
    def _update_conversation_context(self, session_id: str, user_message: str, ai_response: str):
        """Update conversation context"""
        if session_id not in self.conversation_contexts:
            self.conversation_contexts[session_id] = []
        
        self.conversation_contexts[session_id].append({
            "user": user_message,
            "assistant": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only last 10 exchanges to manage memory
        if len(self.conversation_contexts[session_id]) > 10:
            self.conversation_contexts[session_id] = self.conversation_contexts[session_id][-10:]
    
    async def analyze_farming_query(self, query: str) -> Dict:
        """Analyze farming query to extract intent and entities"""
        try:
            query_lower = query.lower()
            
            # Extract crop mentions
            crops_mentioned = []
            for crop in self.knowledge_base["crops"].keys():
                if crop in query_lower:
                    crops_mentioned.append(crop)
            
            # Determine intent
            intent = "general"
            if any(word in query_lower for word in ["disease", "sick", "problem", "spot", "blight"]):
                intent = "disease_diagnosis"
            elif any(word in query_lower for word in ["plant", "grow", "cultivation", "when"]):
                intent = "cultivation_advice"
            elif any(word in query_lower for word in ["weather", "rain", "temperature"]):
                intent = "weather_inquiry"
            elif any(word in query_lower for word in ["soil", "ph", "nutrients", "fertilizer"]):
                intent = "soil_management"
            elif any(word in query_lower for word in ["pest", "insect", "bug"]):
                intent = "pest_management"
            
            # Extract urgency
            urgency = "normal"
            if any(word in query_lower for word in ["urgent", "emergency", "dying", "help"]):
                urgency = "high"
            elif any(word in query_lower for word in ["planning", "future", "next season"]):
                urgency = "low"
            
            return {
                "intent": intent,
                "crops_mentioned": crops_mentioned,
                "urgency": urgency,
                "query_type": self._classify_query_type(query_lower),
                "requires_location": any(word in query_lower for word in ["weather", "climate", "local"]),
                "requires_image": any(word in query_lower for word in ["identify", "what is this", "disease"])
            }
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            return {"intent": "general", "crops_mentioned": [], "urgency": "normal"}
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        if "?" in query:
            return "question"
        elif any(word in query for word in ["help", "advice", "recommend"]):
            return "request_for_advice"
        elif any(word in query for word in ["how to", "how do", "steps"]):
            return "how_to"
        elif any(word in query for word in ["what is", "identify", "tell me"]):
            return "identification"
        else:
            return "statement"
    
    async def get_crop_recommendations(self, location: Dict, season: str) -> Dict:
        """Get crop recommendations based on location and season"""
        try:
            # This would typically use more sophisticated logic based on
            # climate data, soil conditions, and local agricultural practices
            
            recommendations = {
                "spring": ["tomato", "corn", "beans", "lettuce", "spinach"],
                "summer": ["tomato", "corn", "squash", "cucumber", "peppers"],
                "fall": ["wheat", "cabbage", "carrots", "onions", "garlic"],
                "winter": ["winter wheat", "cover crops", "greenhouse vegetables"]
            }
            
            season_crops = recommendations.get(season.lower(), recommendations["spring"])
            
            detailed_recommendations = []
            for crop in season_crops[:5]:  # Top 5 recommendations
                if crop in self.knowledge_base["crops"]:
                    crop_info = self.knowledge_base["crops"][crop]
                    detailed_recommendations.append({
                        "crop": crop,
                        "planting_season": crop_info["planting_season"],
                        "soil_requirements": crop_info["soil_requirements"],
                        "water_needs": crop_info["water_needs"],
                        "harvest_time": crop_info["harvest_time"]
                    })
            
            return {
                "season": season,
                "location": location,
                "recommendations": detailed_recommendations,
                "general_advice": f"For {season} planting, focus on crops that thrive in your local climate conditions."
            }
            
        except Exception as e:
            logger.error(f"Error getting crop recommendations: {e}")
            return {"error": str(e)}
    
    def get_supported_languages(self) -> Dict:
        """Get list of supported languages"""
        return self.supported_languages