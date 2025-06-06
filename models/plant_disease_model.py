"""
Advanced Plant Disease Detection Model
=====================================

This module contains a comprehensive deep learning model for detecting plant diseases
from leaf images. It supports multiple crop types and can identify various diseases
with high accuracy.

Key Features:
- Multi-class disease classification
- Support for 14+ crop types
- 38+ disease categories
- Real-time inference
- Confidence scoring
- Treatment recommendations
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from torchvision.models import efficientnet_b4, EfficientNet_B4_Weights
import numpy as np
from PIL import Image
import json
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlantDiseaseModel(nn.Module):
    """
    Advanced Plant Disease Detection Model based on EfficientNet-B4
    
    This model can classify plant diseases across multiple crop types with
    high accuracy and provides confidence scores for predictions.
    """
    
    def __init__(self, num_classes: int = 38, dropout_rate: float = 0.3):
        super(PlantDiseaseModel, self).__init__()
        
        # Load pre-trained EfficientNet-B4
        self.backbone = efficientnet_b4(weights=EfficientNet_B4_Weights.IMAGENET1K_V1)
        
        # Get the number of features from the classifier
        num_features = self.backbone.classifier[1].in_features
        
        # Replace the classifier with our custom head
        self.backbone.classifier = nn.Sequential(
            nn.Dropout(dropout_rate),
            nn.Linear(num_features, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 256),
            nn.ReLU(inplace=True),
            nn.Dropout(dropout_rate),
            nn.Linear(256, num_classes)
        )
        
        # Disease categories mapping
        self.disease_classes = {
            0: "Apple___Apple_scab",
            1: "Apple___Black_rot",
            2: "Apple___Cedar_apple_rust",
            3: "Apple___healthy",
            4: "Blueberry___healthy",
            5: "Cherry_(including_sour)___Powdery_mildew",
            6: "Cherry_(including_sour)___healthy",
            7: "Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot",
            8: "Corn_(maize)___Common_rust_",
            9: "Corn_(maize)___Northern_Leaf_Blight",
            10: "Corn_(maize)___healthy",
            11: "Grape___Black_rot",
            12: "Grape___Esca_(Black_Measles)",
            13: "Grape___Leaf_blight_(Isariopsis_Leaf_Spot)",
            14: "Grape___healthy",
            15: "Orange___Haunglongbing_(Citrus_greening)",
            16: "Peach___Bacterial_spot",
            17: "Peach___healthy",
            18: "Pepper,_bell___Bacterial_spot",
            19: "Pepper,_bell___healthy",
            20: "Potato___Early_blight",
            21: "Potato___Late_blight",
            22: "Potato___healthy",
            23: "Raspberry___healthy",
            24: "Soybean___healthy",
            25: "Squash___Powdery_mildew",
            26: "Strawberry___Leaf_scorch",
            27: "Strawberry___healthy",
            28: "Tomato___Bacterial_spot",
            29: "Tomato___Early_blight",
            30: "Tomato___Late_blight",
            31: "Tomato___Leaf_Mold",
            32: "Tomato___Septoria_leaf_spot",
            33: "Tomato___Spider_mites Two-spotted_spider_mite",
            34: "Tomato___Target_Spot",
            35: "Tomato___Tomato_Yellow_Leaf_Curl_Virus",
            36: "Tomato___Tomato_mosaic_virus",
            37: "Tomato___healthy"
        }
        
        # Crop types
        self.crop_types = {
            "Apple": [0, 1, 2, 3],
            "Blueberry": [4],
            "Cherry": [5, 6],
            "Corn": [7, 8, 9, 10],
            "Grape": [11, 12, 13, 14],
            "Orange": [15],
            "Peach": [16, 17],
            "Pepper": [18, 19],
            "Potato": [20, 21, 22],
            "Raspberry": [23],
            "Soybean": [24],
            "Squash": [25],
            "Strawberry": [26, 27],
            "Tomato": [28, 29, 30, 31, 32, 33, 34, 35, 36, 37]
        }
        
        # Disease severity mapping
        self.severity_mapping = {
            "healthy": 0,
            "mild": 1,
            "moderate": 2,
            "severe": 3
        }
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the model"""
        return self.backbone(x)
    
    def predict_with_confidence(self, x: torch.Tensor) -> Tuple[int, float, List[Tuple[int, float]]]:
        """
        Make prediction with confidence scores
        
        Args:
            x: Input tensor
            
        Returns:
            Tuple of (predicted_class, confidence, top_5_predictions)
        """
        self.eval()
        with torch.no_grad():
            outputs = self.forward(x)
            probabilities = F.softmax(outputs, dim=1)
            
            # Get top prediction
            confidence, predicted = torch.max(probabilities, 1)
            predicted_class = predicted.item()
            confidence_score = confidence.item()
            
            # Get top 5 predictions
            top5_prob, top5_indices = torch.topk(probabilities, 5, dim=1)
            top5_predictions = [
                (top5_indices[0][i].item(), top5_prob[0][i].item())
                for i in range(5)
            ]
            
            return predicted_class, confidence_score, top5_predictions

class DiseaseDetectionPipeline:
    """
    Complete pipeline for plant disease detection including preprocessing,
    inference, and post-processing.
    """
    
    def __init__(self, model_path: Optional[str] = None, device: str = "auto"):
        """
        Initialize the disease detection pipeline
        
        Args:
            model_path: Path to the trained model weights
            device: Device to run inference on ("cpu", "cuda", or "auto")
        """
        # Set device
        if device == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)
        
        logger.info(f"Using device: {self.device}")
        
        # Initialize model
        self.model = PlantDiseaseModel()
        
        # Load pre-trained weights if available
        if model_path and Path(model_path).exists():
            try:
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                logger.info(f"Loaded model weights from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load model weights: {e}")
                logger.info("Using randomly initialized weights")
        else:
            logger.info("Using randomly initialized weights")
        
        self.model.to(self.device)
        self.model.eval()
        
        # Image preprocessing pipeline
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Load treatment database
        self.treatment_db = self._load_treatment_database()
    
    def _load_treatment_database(self) -> Dict:
        """Load treatment recommendations database"""
        return {
            "Apple___Apple_scab": {
                "description": "Fungal disease causing dark, scabby lesions on leaves and fruit",
                "treatment": [
                    "Apply fungicide sprays during early season",
                    "Remove fallen leaves and infected fruit",
                    "Improve air circulation through pruning",
                    "Use resistant apple varieties"
                ],
                "prevention": [
                    "Plant resistant varieties",
                    "Ensure good air circulation",
                    "Remove infected plant debris",
                    "Apply preventive fungicide sprays"
                ],
                "severity": "moderate"
            },
            "Apple___Black_rot": {
                "description": "Fungal disease causing black rot on fruit and leaf spots",
                "treatment": [
                    "Remove infected fruit and branches",
                    "Apply copper-based fungicides",
                    "Improve orchard sanitation",
                    "Prune for better air circulation"
                ],
                "prevention": [
                    "Regular pruning and sanitation",
                    "Remove mummified fruit",
                    "Apply preventive fungicide treatments",
                    "Avoid overhead irrigation"
                ],
                "severity": "severe"
            },
            "Tomato___Late_blight": {
                "description": "Devastating disease that can destroy entire tomato crops",
                "treatment": [
                    "Apply copper or chlorothalonil fungicides immediately",
                    "Remove infected plants completely",
                    "Improve air circulation",
                    "Avoid overhead watering"
                ],
                "prevention": [
                    "Use certified disease-free seeds",
                    "Provide adequate spacing between plants",
                    "Water at soil level, not on leaves",
                    "Apply preventive fungicide sprays"
                ],
                "severity": "severe"
            },
            "Potato___Late_blight": {
                "description": "Same pathogen as tomato late blight, highly destructive",
                "treatment": [
                    "Apply systemic fungicides immediately",
                    "Destroy infected plants",
                    "Harvest tubers before disease spreads",
                    "Improve field drainage"
                ],
                "prevention": [
                    "Use certified seed potatoes",
                    "Plant in well-draining soil",
                    "Avoid overhead irrigation",
                    "Monitor weather conditions for disease-favorable periods"
                ],
                "severity": "severe"
            },
            # Add more diseases as needed...
        }
    
    def preprocess_image(self, image_path: str) -> torch.Tensor:
        """
        Preprocess image for model inference
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Preprocessed image tensor
        """
        try:
            # Load and convert image
            image = Image.open(image_path).convert('RGB')
            
            # Apply transformations
            image_tensor = self.transform(image)
            
            # Add batch dimension
            image_tensor = image_tensor.unsqueeze(0)
            
            return image_tensor.to(self.device)
        
        except Exception as e:
            logger.error(f"Error preprocessing image {image_path}: {e}")
            raise
    
    def detect_disease(self, image_path: str) -> Dict:
        """
        Detect plant disease from image
        
        Args:
            image_path: Path to the input image
            
        Returns:
            Dictionary containing detection results
        """
        try:
            # Preprocess image
            image_tensor = self.preprocess_image(image_path)
            
            # Make prediction
            predicted_class, confidence, top5_predictions = self.model.predict_with_confidence(image_tensor)
            
            # Get disease name
            disease_name = self.model.disease_classes[predicted_class]
            
            # Extract crop and disease information
            crop_name, disease_type = self._parse_disease_name(disease_name)
            
            # Get treatment recommendations
            treatment_info = self.treatment_db.get(disease_name, {
                "description": "Disease information not available",
                "treatment": ["Consult with agricultural expert"],
                "prevention": ["Follow general plant care practices"],
                "severity": "unknown"
            })
            
            # Prepare results
            results = {
                "disease_detected": disease_name,
                "crop_type": crop_name,
                "disease_type": disease_type,
                "confidence": round(confidence * 100, 2),
                "is_healthy": "healthy" in disease_name.lower(),
                "severity": treatment_info.get("severity", "unknown"),
                "description": treatment_info.get("description", ""),
                "treatment_recommendations": treatment_info.get("treatment", []),
                "prevention_tips": treatment_info.get("prevention", []),
                "top_predictions": [
                    {
                        "disease": self.model.disease_classes[class_idx],
                        "confidence": round(conf * 100, 2)
                    }
                    for class_idx, conf in top5_predictions
                ],
                "model_info": {
                    "model_type": "EfficientNet-B4",
                    "num_classes": len(self.model.disease_classes),
                    "device": str(self.device)
                }
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error detecting disease: {e}")
            return {
                "error": str(e),
                "disease_detected": "unknown",
                "confidence": 0.0,
                "is_healthy": False
            }
    
    def _parse_disease_name(self, disease_name: str) -> Tuple[str, str]:
        """
        Parse disease name to extract crop and disease type
        
        Args:
            disease_name: Full disease name from model
            
        Returns:
            Tuple of (crop_name, disease_type)
        """
        parts = disease_name.split("___")
        if len(parts) >= 2:
            crop_name = parts[0].replace("_", " ").title()
            disease_type = parts[1].replace("_", " ").title()
        else:
            crop_name = "Unknown"
            disease_type = disease_name.replace("_", " ").title()
        
        return crop_name, disease_type
    
    def batch_detect(self, image_paths: List[str]) -> List[Dict]:
        """
        Detect diseases in multiple images
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of detection results
        """
        results = []
        for image_path in image_paths:
            result = self.detect_disease(image_path)
            result["image_path"] = image_path
            results.append(result)
        
        return results
    
    def get_crop_health_summary(self, image_paths: List[str]) -> Dict:
        """
        Generate health summary for multiple crop images
        
        Args:
            image_paths: List of image paths
            
        Returns:
            Health summary statistics
        """
        results = self.batch_detect(image_paths)
        
        total_images = len(results)
        healthy_count = sum(1 for r in results if r.get("is_healthy", False))
        diseased_count = total_images - healthy_count
        
        # Count diseases by type
        disease_counts = {}
        crop_counts = {}
        
        for result in results:
            if not result.get("is_healthy", False):
                disease = result.get("disease_type", "Unknown")
                disease_counts[disease] = disease_counts.get(disease, 0) + 1
            
            crop = result.get("crop_type", "Unknown")
            crop_counts[crop] = crop_counts.get(crop, 0) + 1
        
        return {
            "total_images": total_images,
            "healthy_plants": healthy_count,
            "diseased_plants": diseased_count,
            "health_percentage": round((healthy_count / total_images) * 100, 2) if total_images > 0 else 0,
            "disease_distribution": disease_counts,
            "crop_distribution": crop_counts,
            "recommendations": self._generate_field_recommendations(results)
        }
    
    def _generate_field_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate field-level recommendations based on detection results"""
        recommendations = []
        
        diseased_results = [r for r in results if not r.get("is_healthy", False)]
        
        if not diseased_results:
            recommendations.append("Crops appear healthy. Continue current management practices.")
            return recommendations
        
        # Count severe diseases
        severe_diseases = [r for r in diseased_results if r.get("severity") == "severe"]
        
        if severe_diseases:
            recommendations.append("URGENT: Severe diseases detected. Immediate intervention required.")
            recommendations.append("Isolate affected plants to prevent spread.")
        
        # Common diseases
        disease_counts = {}
        for result in diseased_results:
            disease = result.get("disease_type", "Unknown")
            disease_counts[disease] = disease_counts.get(disease, 0) + 1
        
        if disease_counts:
            most_common = max(disease_counts, key=disease_counts.get)
            recommendations.append(f"Most common issue: {most_common}")
            recommendations.append("Consider field-wide preventive measures.")
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    # Initialize the pipeline
    pipeline = DiseaseDetectionPipeline()
    
    # Example detection (would need actual image file)
    # result = pipeline.detect_disease("path/to/plant/image.jpg")
    # print(json.dumps(result, indent=2))
    
    print("Plant Disease Detection Model initialized successfully!")
    print(f"Model supports {len(pipeline.model.disease_classes)} disease classes")
    print(f"Supported crops: {list(pipeline.model.crop_types.keys())}")