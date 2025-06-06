"""
Disease Detection API routes
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db, User, DiseaseScan
from ...core.security import get_current_active_user
from ...core.config import settings

router = APIRouter()

# Pydantic models
class DiseaseDetectionResponse(BaseModel):
    scan_id: int
    predicted_disease: str
    confidence: float
    severity: str
    description: str
    treatment: str
    prevention: list
    image_quality: dict
    treatment_plan: dict
    created_at: datetime

class ScanHistoryResponse(BaseModel):
    id: int
    predicted_disease: str
    confidence_score: float
    created_at: datetime
    latitude: Optional[float]
    longitude: Optional[float]

@router.post("/analyze", response_model=DiseaseDetectionResponse)
async def analyze_plant_disease(
    request: Request,
    image: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze plant image for disease detection"""
    
    # Validate file type
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Validate file size
    if image.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    try:
        # Save uploaded image
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Get disease detector from app state
        disease_detector = request.app.state.disease_detector
        
        # Analyze the image
        analysis_result = await disease_detector.detect_disease(file_path)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # Get detailed treatment plan
        treatment_plan = await disease_detector.get_treatment_plan(
            analysis_result["predicted_disease"],
            analysis_result.get("severity", "moderate")
        )
        
        # Save scan result to database
        scan_record = DiseaseScan(
            user_id=current_user.id,
            image_path=file_path,
            predicted_disease=analysis_result["predicted_disease"],
            confidence_score=analysis_result["confidence"],
            treatment_recommendation=analysis_result.get("treatment", ""),
            latitude=latitude,
            longitude=longitude
        )
        
        db.add(scan_record)
        db.commit()
        db.refresh(scan_record)
        
        # Prepare response
        response = DiseaseDetectionResponse(
            scan_id=scan_record.id,
            predicted_disease=analysis_result["predicted_disease"],
            confidence=analysis_result["confidence"],
            severity=analysis_result.get("severity", "unknown"),
            description=analysis_result.get("description", ""),
            treatment=analysis_result.get("treatment", ""),
            prevention=analysis_result.get("prevention", []),
            image_quality=analysis_result.get("image_quality", {}),
            treatment_plan=treatment_plan,
            created_at=scan_record.created_at
        )
        
        return response
        
    except Exception as e:
        # Clean up uploaded file if analysis failed
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.get("/history", response_model=list[ScanHistoryResponse])
async def get_scan_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20,
    offset: int = 0
):
    """Get user's disease detection history"""
    
    scans = db.query(DiseaseScan).filter(
        DiseaseScan.user_id == current_user.id
    ).order_by(
        DiseaseScan.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [
        ScanHistoryResponse(
            id=scan.id,
            predicted_disease=scan.predicted_disease or "Unknown",
            confidence_score=scan.confidence_score or 0.0,
            created_at=scan.created_at,
            latitude=scan.latitude,
            longitude=scan.longitude
        )
        for scan in scans
    ]

@router.get("/scan/{scan_id}", response_model=DiseaseDetectionResponse)
async def get_scan_details(
    scan_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific scan"""
    
    scan = db.query(DiseaseScan).filter(
        DiseaseScan.id == scan_id,
        DiseaseScan.user_id == current_user.id
    ).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get disease detector for additional analysis
    disease_detector = request.app.state.disease_detector
    
    # Get treatment plan
    treatment_plan = await disease_detector.get_treatment_plan(
        scan.predicted_disease or "unknown",
        "moderate"  # Default severity
    )
    
    # Mock image quality data (in real app, this would be stored)
    image_quality = {
        "quality_score": 75,
        "issues": [],
        "recommendations": ["Image quality is acceptable for analysis"]
    }
    
    return DiseaseDetectionResponse(
        scan_id=scan.id,
        predicted_disease=scan.predicted_disease or "Unknown",
        confidence=scan.confidence_score or 0.0,
        severity="moderate",  # Would be stored in database in real app
        description="Disease analysis result",
        treatment=scan.treatment_recommendation or "",
        prevention=[],  # Would be stored in database in real app
        image_quality=image_quality,
        treatment_plan=treatment_plan,
        created_at=scan.created_at
    )

@router.delete("/scan/{scan_id}")
async def delete_scan(
    scan_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a scan record"""
    
    scan = db.query(DiseaseScan).filter(
        DiseaseScan.id == scan_id,
        DiseaseScan.user_id == current_user.id
    ).first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Delete image file
    if os.path.exists(scan.image_path):
        try:
            os.remove(scan.image_path)
        except Exception as e:
            # Log error but don't fail the deletion
            pass
    
    # Delete database record
    db.delete(scan)
    db.commit()
    
    return {"message": "Scan deleted successfully"}

@router.get("/diseases/info")
async def get_disease_info(
    request: Request,
    current_user: User = Depends(get_current_active_user)
):
    """Get information about detectable diseases"""
    
    disease_detector = request.app.state.disease_detector
    
    return {
        "supported_diseases": list(disease_detector.disease_info.keys()),
        "disease_details": disease_detector.disease_info,
        "model_info": {
            "confidence_threshold": settings.MODEL_CONFIDENCE_THRESHOLD,
            "supported_formats": settings.ALLOWED_IMAGE_TYPES
        }
    }

@router.get("/public/diseases/info")
async def get_disease_info_public(request: Request):
    """Get basic information about detectable diseases (public access)"""
    
    disease_detector = request.app.state.disease_detector
    
    # Return limited information for public access
    return {
        "supported_diseases": list(disease_detector.disease_info.keys()),
        "disease_count": len(disease_detector.disease_info),
        "model_info": {
            "confidence_threshold": settings.MODEL_CONFIDENCE_THRESHOLD,
            "supported_formats": settings.ALLOWED_IMAGE_TYPES
        },
        "note": "For detailed disease information, please register and login."
    }

@router.post("/batch-analyze")
async def batch_analyze_images(
    request: Request,
    images: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze multiple images in batch"""
    
    if len(images) > 10:  # Limit batch size
        raise HTTPException(status_code=400, detail="Maximum 10 images per batch")
    
    results = []
    disease_detector = request.app.state.disease_detector
    
    for image in images:
        try:
            # Validate file
            if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
                results.append({
                    "filename": image.filename,
                    "error": "Invalid file type"
                })
                continue
            
            # Save and analyze
            file_extension = os.path.splitext(image.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)
            
            with open(file_path, "wb") as buffer:
                content = await image.read()
                buffer.write(content)
            
            # Analyze
            analysis_result = await disease_detector.detect_disease(file_path)
            
            # Save to database
            scan_record = DiseaseScan(
                user_id=current_user.id,
                image_path=file_path,
                predicted_disease=analysis_result.get("predicted_disease", "Unknown"),
                confidence_score=analysis_result.get("confidence", 0.0),
                treatment_recommendation=analysis_result.get("treatment", "")
            )
            
            db.add(scan_record)
            db.commit()
            db.refresh(scan_record)
            
            results.append({
                "filename": image.filename,
                "scan_id": scan_record.id,
                "predicted_disease": analysis_result.get("predicted_disease", "Unknown"),
                "confidence": analysis_result.get("confidence", 0.0)
            })
            
        except Exception as e:
            results.append({
                "filename": image.filename,
                "error": str(e)
            })
    
    return {"results": results}

@router.post("/public/analyze")
async def analyze_plant_disease_public(
    request: Request,
    image: UploadFile = File(...),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None)
):
    """Analyze plant image for disease detection (public access with demo results)
    
    Note: This endpoint provides demo results only. For real analysis and data storage,
    please register and use the authenticated endpoint.
    """
    
    # Validate file type
    if image.content_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Validate file size
    if image.size > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    try:
        # For demo purposes, generate realistic mock results
        import random
        from datetime import datetime
        
        # Common plant diseases for demo
        diseases = [
            {
                "name": "Healthy Plant",
                "confidence": random.uniform(0.85, 0.95),
                "severity": "none",
                "description": "The plant appears healthy with no visible signs of disease.",
                "treatment": "Continue regular care and monitoring.",
                "prevention": [
                    "Maintain proper watering schedule",
                    "Ensure adequate sunlight",
                    "Regular inspection for early detection"
                ]
            },
            {
                "name": "Leaf Spot Disease",
                "confidence": random.uniform(0.75, 0.90),
                "severity": "moderate",
                "description": "Fungal infection causing circular spots on leaves.",
                "treatment": "Apply fungicide spray and remove affected leaves.",
                "prevention": [
                    "Improve air circulation",
                    "Avoid overhead watering",
                    "Remove fallen leaves regularly"
                ]
            },
            {
                "name": "Powdery Mildew",
                "confidence": random.uniform(0.70, 0.85),
                "severity": "mild",
                "description": "White powdery coating on leaves and stems.",
                "treatment": "Apply sulfur-based fungicide or neem oil.",
                "prevention": [
                    "Ensure good air circulation",
                    "Avoid overcrowding plants",
                    "Water at soil level"
                ]
            },
            {
                "name": "Bacterial Blight",
                "confidence": random.uniform(0.65, 0.80),
                "severity": "severe",
                "description": "Bacterial infection causing brown spots and wilting.",
                "treatment": "Remove infected parts and apply copper-based bactericide.",
                "prevention": [
                    "Use disease-free seeds",
                    "Avoid working with wet plants",
                    "Rotate crops annually"
                ]
            }
        ]
        
        # Randomly select a disease (weighted towards healthy)
        weights = [0.4, 0.25, 0.20, 0.15]  # Higher chance of healthy plant
        selected_disease = random.choices(diseases, weights=weights)[0]
        
        # Generate image quality assessment
        quality_score = random.randint(70, 95)
        quality_issues = []
        quality_recommendations = []
        
        if quality_score < 80:
            quality_issues.extend(["Image could be clearer", "Lighting could be improved"])
            quality_recommendations.extend(["Use better lighting", "Hold camera steady"])
        else:
            quality_recommendations.append("Image quality is good for analysis")
        
        # Generate treatment plan
        treatment_plan = {
            "immediate_actions": [
                selected_disease["treatment"],
                "Monitor plant daily for changes"
            ],
            "weekly_care": [
                "Check for new symptoms",
                "Maintain proper watering"
            ],
            "preventive_measures": selected_disease["prevention"]
        }
        
        return {
            "scan_id": random.randint(1000, 9999),
            "predicted_disease": selected_disease["name"],
            "confidence": selected_disease["confidence"],
            "severity": selected_disease["severity"],
            "description": selected_disease["description"],
            "treatment": selected_disease["treatment"],
            "prevention": selected_disease["prevention"],
            "image_quality": {
                "quality_score": quality_score,
                "issues": quality_issues,
                "recommendations": quality_recommendations
            },
            "treatment_plan": treatment_plan,
            "location": f"📍 {latitude:.2f}°, {longitude:.2f}°" if latitude and longitude else "Location not provided",
            "data_source": "🔄 Demo Analysis (Add trained models for real detection)",
            "created_at": datetime.utcnow().isoformat(),
            "demo_mode": True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")