"""
Plant Disease Detection using Computer Vision
Enhanced with YOLOv8 and custom CNN models
"""

import os
import cv2
import numpy as np
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import logging
from typing import Dict, List, Tuple, Optional
from ultralytics import YOLO
import asyncio
from concurrent.futures import ThreadPoolExecutor

from ..core.config import settings

logger = logging.getLogger(__name__)

class DiseaseDetector:
    """Advanced plant disease detection system"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.yolo_model = None
        self.classification_model = None
        self.class_names = []
        self.disease_info = {}
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        # Image preprocessing pipeline
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                               std=[0.229, 0.224, 0.225])
        ])
        
        self._load_disease_database()
    
    def _load_disease_database(self):
        """Load disease information database"""
        self.disease_info = {
            "healthy": {
                "name": "Healthy Plant",
                "description": "The plant appears to be healthy with no visible signs of disease.",
                "treatment": "Continue regular care and monitoring.",
                "severity": "none",
                "prevention": [
                    "Maintain proper watering schedule",
                    "Ensure adequate sunlight",
                    "Regular inspection for early detection"
                ]
            },
            "bacterial_spot": {
                "name": "Bacterial Spot",
                "description": "Bacterial infection causing dark spots on leaves and fruits.",
                "treatment": "Apply copper-based fungicides and remove affected parts.",
                "severity": "moderate",
                "prevention": [
                    "Avoid overhead watering",
                    "Improve air circulation",
                    "Use disease-resistant varieties"
                ]
            },
            "early_blight": {
                "name": "Early Blight",
                "description": "Fungal disease causing brown spots with concentric rings.",
                "treatment": "Apply fungicides containing chlorothalonil or copper.",
                "severity": "moderate",
                "prevention": [
                    "Crop rotation",
                    "Remove plant debris",
                    "Avoid overhead irrigation"
                ]
            },
            "late_blight": {
                "name": "Late Blight",
                "description": "Serious fungal disease that can destroy entire crops quickly.",
                "treatment": "Immediate application of systemic fungicides.",
                "severity": "severe",
                "prevention": [
                    "Use certified disease-free seeds",
                    "Ensure good drainage",
                    "Monitor weather conditions"
                ]
            },
            "leaf_mold": {
                "name": "Leaf Mold",
                "description": "Fungal disease causing yellow spots that turn brown.",
                "treatment": "Improve ventilation and apply appropriate fungicides.",
                "severity": "moderate",
                "prevention": [
                    "Reduce humidity",
                    "Increase air circulation",
                    "Avoid overcrowding plants"
                ]
            },
            "septoria_leaf_spot": {
                "name": "Septoria Leaf Spot",
                "description": "Fungal disease causing small circular spots with dark borders.",
                "treatment": "Remove affected leaves and apply fungicides.",
                "severity": "moderate",
                "prevention": [
                    "Mulch around plants",
                    "Water at soil level",
                    "Practice crop rotation"
                ]
            },
            "spider_mites": {
                "name": "Spider Mites",
                "description": "Tiny pests that cause stippling and webbing on leaves.",
                "treatment": "Use miticides or insecticidal soaps.",
                "severity": "moderate",
                "prevention": [
                    "Maintain adequate humidity",
                    "Regular inspection",
                    "Biological control with predatory mites"
                ]
            },
            "target_spot": {
                "name": "Target Spot",
                "description": "Fungal disease causing circular spots with target-like appearance.",
                "treatment": "Apply fungicides and improve air circulation.",
                "severity": "moderate",
                "prevention": [
                    "Avoid overhead watering",
                    "Remove infected plant material",
                    "Use resistant varieties"
                ]
            },
            "mosaic_virus": {
                "name": "Mosaic Virus",
                "description": "Viral disease causing mottled yellow and green patterns.",
                "treatment": "No cure available; remove infected plants.",
                "severity": "severe",
                "prevention": [
                    "Control aphid vectors",
                    "Use virus-free seeds",
                    "Sanitize tools between plants"
                ]
            },
            "yellow_leaf_curl": {
                "name": "Yellow Leaf Curl Virus",
                "description": "Viral disease causing yellowing and curling of leaves.",
                "treatment": "Remove infected plants and control whitefly vectors.",
                "severity": "severe",
                "prevention": [
                    "Use reflective mulches",
                    "Control whitefly populations",
                    "Use resistant varieties"
                ]
            }
        }
        
        self.class_names = list(self.disease_info.keys())
    
    async def load_model(self):
        """Load the disease detection models"""
        try:
            # Try to load custom trained model first
            if os.path.exists(settings.DISEASE_MODEL_PATH):
                logger.info("Loading custom disease detection model...")
                self.classification_model = await self._load_custom_model()
            else:
                logger.info("Loading pre-trained model...")
                self.classification_model = await self._load_pretrained_model()
            
            # Load YOLO for plant detection and localization
            try:
                self.yolo_model = YOLO('yolov8n.pt')  # Lightweight version
                logger.info("YOLO model loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load YOLO model: {e}")
            
            logger.info("Disease detection models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            # Fallback to a simple model
            self.classification_model = await self._create_fallback_model()
    
    async def _load_custom_model(self):
        """Load custom trained model"""
        def _load():
            model = models.resnet50(pretrained=False)
            model.fc = nn.Linear(model.fc.in_features, len(self.class_names))
            model.load_state_dict(torch.load(settings.DISEASE_MODEL_PATH, map_location=self.device))
            model.to(self.device)
            model.eval()
            return model
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _load)
    
    async def _load_pretrained_model(self):
        """Load and adapt pre-trained model"""
        def _load():
            model = models.resnet50(pretrained=True)
            model.fc = nn.Linear(model.fc.in_features, len(self.class_names))
            model.to(self.device)
            model.eval()
            return model
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _load)
    
    async def _create_fallback_model(self):
        """Create a simple fallback model"""
        def _create():
            model = models.mobilenet_v2(pretrained=True)
            model.classifier = nn.Sequential(
                nn.Dropout(0.2),
                nn.Linear(model.last_channel, len(self.class_names))
            )
            model.to(self.device)
            model.eval()
            return model
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _create)
    
    async def detect_disease(self, image_path: str) -> Dict:
        """
        Detect plant diseases in an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing detection results
        """
        try:
            # Load and preprocess image
            image = await self._load_and_preprocess_image(image_path)
            
            # Detect plants in image using YOLO (if available)
            plant_regions = await self._detect_plants(image_path)
            
            # Classify disease
            predictions = await self._classify_disease(image)
            
            # Get top prediction
            top_prediction = predictions[0]
            disease_key = top_prediction['class']
            confidence = top_prediction['confidence']
            
            # Get disease information
            disease_info = self.disease_info.get(disease_key, {})
            
            # Prepare result
            result = {
                "predicted_disease": disease_info.get("name", "Unknown"),
                "confidence": float(confidence),
                "severity": disease_info.get("severity", "unknown"),
                "description": disease_info.get("description", ""),
                "treatment": disease_info.get("treatment", ""),
                "prevention": disease_info.get("prevention", []),
                "all_predictions": predictions,
                "plant_regions_detected": len(plant_regions) if plant_regions else 0,
                "image_quality": await self._assess_image_quality(image_path)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in disease detection: {e}")
            return {
                "error": str(e),
                "predicted_disease": "Error",
                "confidence": 0.0
            }
    
    async def _load_and_preprocess_image(self, image_path: str) -> torch.Tensor:
        """Load and preprocess image for model input"""
        def _process():
            image = Image.open(image_path).convert('RGB')
            return self.transform(image).unsqueeze(0).to(self.device)
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _process)
    
    async def _detect_plants(self, image_path: str) -> List[Dict]:
        """Detect plant regions using YOLO"""
        if not self.yolo_model:
            return []
        
        def _detect():
            try:
                results = self.yolo_model(image_path)
                plant_regions = []
                
                for result in results:
                    boxes = result.boxes
                    if boxes is not None:
                        for box in boxes:
                            # Filter for plant-related classes
                            class_id = int(box.cls[0])
                            confidence = float(box.conf[0])
                            
                            if confidence > 0.5:  # Confidence threshold
                                x1, y1, x2, y2 = box.xyxy[0].tolist()
                                plant_regions.append({
                                    "bbox": [x1, y1, x2, y2],
                                    "confidence": confidence,
                                    "class_id": class_id
                                })
                
                return plant_regions
            except Exception as e:
                logger.warning(f"YOLO detection failed: {e}")
                return []
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _detect)
    
    async def _classify_disease(self, image_tensor: torch.Tensor) -> List[Dict]:
        """Classify disease in the image"""
        def _classify():
            with torch.no_grad():
                outputs = self.classification_model(image_tensor)
                probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
                
                # Get top 3 predictions
                top_probs, top_indices = torch.topk(probabilities, min(3, len(self.class_names)))
                
                predictions = []
                for i in range(len(top_probs)):
                    class_idx = top_indices[i].item()
                    confidence = top_probs[i].item()
                    
                    if class_idx < len(self.class_names):
                        predictions.append({
                            "class": self.class_names[class_idx],
                            "confidence": confidence,
                            "class_index": class_idx
                        })
                
                return predictions
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _classify)
    
    async def _assess_image_quality(self, image_path: str) -> Dict:
        """Assess image quality for better diagnosis"""
        def _assess():
            try:
                image = cv2.imread(image_path)
                
                # Calculate blur metric (Laplacian variance)
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                blur_metric = cv2.Laplacian(gray, cv2.CV_64F).var()
                
                # Calculate brightness
                brightness = np.mean(gray)
                
                # Calculate contrast
                contrast = gray.std()
                
                # Assess overall quality
                quality_score = 0
                issues = []
                
                if blur_metric < 100:
                    issues.append("Image appears blurry")
                else:
                    quality_score += 25
                
                if brightness < 50:
                    issues.append("Image is too dark")
                elif brightness > 200:
                    issues.append("Image is too bright")
                else:
                    quality_score += 25
                
                if contrast < 30:
                    issues.append("Low contrast")
                else:
                    quality_score += 25
                
                # Check image size
                height, width = image.shape[:2]
                if width < 224 or height < 224:
                    issues.append("Image resolution is too low")
                else:
                    quality_score += 25
                
                return {
                    "quality_score": quality_score,
                    "blur_metric": float(blur_metric),
                    "brightness": float(brightness),
                    "contrast": float(contrast),
                    "resolution": f"{width}x{height}",
                    "issues": issues,
                    "recommendations": self._get_quality_recommendations(quality_score, issues)
                }
                
            except Exception as e:
                logger.error(f"Error assessing image quality: {e}")
                return {"quality_score": 0, "error": str(e)}
        
        return await asyncio.get_event_loop().run_in_executor(self.executor, _assess)
    
    def _get_quality_recommendations(self, quality_score: int, issues: List[str]) -> List[str]:
        """Get recommendations for improving image quality"""
        recommendations = []
        
        if quality_score < 50:
            recommendations.append("Consider retaking the photo with better lighting")
        
        if "blurry" in " ".join(issues).lower():
            recommendations.append("Hold the camera steady and ensure proper focus")
        
        if "dark" in " ".join(issues).lower():
            recommendations.append("Take photo in better lighting conditions")
        
        if "bright" in " ".join(issues).lower():
            recommendations.append("Avoid direct sunlight, use diffused lighting")
        
        if "resolution" in " ".join(issues).lower():
            recommendations.append("Use a higher resolution camera or get closer to the plant")
        
        if not recommendations:
            recommendations.append("Image quality is good for analysis")
        
        return recommendations
    
    async def get_treatment_plan(self, disease: str, severity: str = "moderate") -> Dict:
        """Get detailed treatment plan for a specific disease"""
        disease_info = self.disease_info.get(disease.lower().replace(" ", "_"), {})
        
        base_plan = {
            "immediate_actions": [],
            "short_term": [],
            "long_term": [],
            "monitoring": [],
            "prevention": disease_info.get("prevention", [])
        }
        
        if severity == "severe":
            base_plan["immediate_actions"] = [
                "Isolate affected plants immediately",
                "Remove and destroy infected plant material",
                "Apply emergency treatment if available"
            ]
        elif severity == "moderate":
            base_plan["immediate_actions"] = [
                "Remove affected leaves/parts",
                "Improve growing conditions",
                "Begin treatment regimen"
            ]
        else:
            base_plan["immediate_actions"] = [
                "Monitor closely for progression",
                "Adjust care routine as needed"
            ]
        
        base_plan["short_term"] = [
            "Apply recommended treatments",
            "Monitor plant response",
            "Adjust environmental conditions"
        ]
        
        base_plan["long_term"] = [
            "Implement prevention strategies",
            "Regular health monitoring",
            "Consider resistant varieties for future planting"
        ]
        
        base_plan["monitoring"] = [
            "Check plants daily for changes",
            "Document treatment progress",
            "Watch for spread to other plants"
        ]
        
        return base_plan