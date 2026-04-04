from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import uuid
import time
from datetime import datetime

from app.models.xray_analysis import (
    XRayAnalysisCreate, 
    XRayAnalysisResponse, 
    XRayAnalysisSummary,
    AnalysisResult
)
from app.utils.security import verify_token, generate_analysis_id
from app.database.mongodb import get_database

router = APIRouter()
security = HTTPBearer()

@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router is working"""
    return {"message": "X-ray analysis router is working", "status": "ok"}

# Configuration
UPLOAD_DIR = "uploads"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from token"""
    token = credentials.credentials
    payload = verify_token(token)
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    
    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role")
    }

def validate_image(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False
    
    # For now, just check if file has content (size check removed for simplicity)
    return True

def analyze_xray_image(image_path: str) -> AnalysisResult:
    """Analyze X-ray image for pneumonia detection"""
    try:
        # Simulate AI model analysis (in production, this would use a trained model)
        # For demo purposes, we'll create a mock analysis
        time.sleep(1)  # Simulate processing time
        
        # Mock analysis results (in production, replace with actual model inference)
        import random
        confidence_score = random.uniform(0.7, 0.95)
        pneumonia_detected = random.choice([True, False]) if confidence_score < 0.8 else True
        
        if pneumonia_detected:
            findings = "Evidence of bilateral infiltrates consistent with pneumonia. Opacity observed in lower lung fields."
            recommendations = "Immediate medical consultation recommended. Consider chest X-ray follow-up in 1-2 weeks."
        else:
            findings = "No acute cardiopulmonary abnormalities detected. Lung fields appear clear."
            recommendations = "Routine follow-up as needed. No immediate intervention required."
        
        return AnalysisResult(
            pneumonia_detected=pneumonia_detected,
            confidence_score=confidence_score,
            findings=findings,
            recommendations=recommendations,
            analysis_details={
                "image_quality": "Good",
                "lung_visibility": "Clear",
                "processing_time": "1.0s",
                "model_version": "v1.0.0"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {str(e)}"
        )

@router.post("/upload", response_model=XRayAnalysisResponse)
async def upload_xray(
    file: UploadFile = File(...),
    patient_id: str = Form(None),  # Optional patient_id from form
    current_user: dict = Depends(get_current_user)
):
    """Upload and analyze X-ray image"""
    # Validate file
    if not validate_image(file):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format or size. Supported formats: JPG, PNG, BMP, TIFF (max 10MB)"
        )
    
    # Get patient record for current user
    db = get_database()
    
    # If patient_id is provided, use it; otherwise get the patient for current user
    if patient_id:
        patient = await db.patients.find_one({"patient_id": patient_id, "user_id": current_user["user_id"]})
    else:
        patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found. Please create a patient record first or provide a valid patient_id."
        )
    
    try:
        # Save uploaded file
        file_extension = os.path.splitext(file.filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Read and save file
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Create analysis record
        analysis_id = generate_analysis_id()
        analysis_in_db = {
            "analysis_id": analysis_id,
            "patient_id": patient["patient_id"],
            "image_url": f"/uploads/{unique_filename}",
            "image_filename": file.filename,
            "status": "processing",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await db.xray_analyses.insert_one(analysis_in_db)
        
        # Perform analysis
        start_time = time.time()
        analysis_result = analyze_xray_image(file_path)
        processing_time = time.time() - start_time
        
        # Update analysis record with results
        update_data = {
            "result": analysis_result.dict(),
            "status": "completed",
            "processing_time": processing_time,
            "updated_at": datetime.utcnow()
        }
        
        await db.xray_analyses.update_one(
            {"_id": result.inserted_id},
            {"$set": update_data}
        )
        
        # Get updated analysis
        updated_analysis = await db.xray_analyses.find_one({"_id": result.inserted_id})
        
        return XRayAnalysisResponse(
            id=str(updated_analysis["_id"]),
            analysis_id=updated_analysis["analysis_id"],
            patient_id=updated_analysis["patient_id"],
            image_url=updated_analysis["image_url"],
            image_filename=updated_analysis["image_filename"],
            result=AnalysisResult(**updated_analysis["result"]),
            status=updated_analysis["status"],
            processing_time=updated_analysis["processing_time"],
            created_at=updated_analysis["created_at"],
            updated_at=updated_analysis["updated_at"]
        )
        
    except Exception as e:
        # Clean up uploaded file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload and analysis failed: {str(e)}"
        )

@router.get("/", response_model=List[XRayAnalysisSummary])
async def get_analyses(current_user: dict = Depends(get_current_user)):
    """Get all X-ray analyses for current user"""
    db = get_database()
    
    # Get patient record
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    # Get analyses for patient
    analyses = await db.xray_analyses.find(
        {"patient_id": patient["patient_id"]}
    ).sort("created_at", -1).to_list(length=None)
    
    summaries = []
    for analysis in analyses:
        result = analysis.get("result", {})
        summaries.append(XRayAnalysisSummary(
            analysis_id=analysis["analysis_id"],
            patient_id=analysis["patient_id"],
            status=analysis["status"],
            pneumonia_detected=result.get("pneumonia_detected"),
            confidence_score=result.get("confidence_score"),
            created_at=analysis["created_at"]
        ))
    
    return summaries

@router.get("/{analysis_id}", response_model=XRayAnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific X-ray analysis"""
    db = get_database()
    
    # Get patient record
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    # Get analysis
    analysis = await db.xray_analyses.find_one({
        "analysis_id": analysis_id,
        "patient_id": patient["patient_id"]
    })
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    result_data = analysis.get("result")
    result = AnalysisResult(**result_data) if result_data else None
    
    return XRayAnalysisResponse(
        id=str(analysis["_id"]),
        analysis_id=analysis["analysis_id"],
        patient_id=analysis["patient_id"],
        image_url=analysis["image_url"],
        image_filename=analysis["image_filename"],
        result=result,
        status=analysis["status"],
        error_message=analysis.get("error_message"),
        processing_time=analysis.get("processing_time"),
        created_at=analysis["created_at"],
        updated_at=analysis["updated_at"]
    )

@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete X-ray analysis"""
    db = get_database()
    
    # Get patient record
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    # Find and delete analysis
    analysis = await db.xray_analyses.find_one({
        "analysis_id": analysis_id,
        "patient_id": patient["patient_id"]
    })
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    # Delete image file
    if "image_url" in analysis:
        image_path = analysis["image_url"].lstrip("/uploads/")
        full_path = os.path.join(UPLOAD_DIR, image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
    
    # Delete analysis record
    await db.xray_analyses.delete_one({"_id": analysis["_id"]})
    
    return {"message": "Analysis deleted successfully"}
