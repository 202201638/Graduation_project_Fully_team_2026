from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.models.patient import PatientCreate, PatientResponse, PatientUpdate, PatientInDB
from app.models.user import UserResponse
from app.utils.security import verify_token, generate_patient_id
from app.database.mongodb import require_database

# Pydantic models for medical data
class MedicalHistoryRequest(BaseModel):
    medical_history: str

class AllergyRequest(BaseModel):
    allergy: str

class MedicationRequest(BaseModel):
    medication: str

router = APIRouter()
security = HTTPBearer()

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

@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient_data: PatientCreate, current_user: dict = Depends(get_current_user)):
    """Create a new patient record"""
    db = require_database()
    
    # Verify user exists and has permission
    user = await db.users.find_one({"user_id": current_user["user_id"]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if patient already exists for this user
    existing_patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient record already exists for this user"
        )
    
    # Create new patient
    patient_id = generate_patient_id()
    patient_in_db = PatientInDB(
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=patient_data.date_of_birth,
        gender=patient_data.gender,
        phone=patient_data.phone,
        address=patient_data.address,
        emergency_contact=patient_data.emergency_contact,
        patient_id=patient_id,
        user_id=current_user["user_id"]
    )
    
    # Insert into database
    patient_dict = patient_in_db.dict(by_alias=True)
    result = await db.patients.insert_one(patient_dict)
    
    # Return patient response
    return PatientResponse(
        id=str(result.inserted_id),
        patient_id=patient_id,
        user_id=current_user["user_id"],
        first_name=patient_data.first_name,
        last_name=patient_data.last_name,
        date_of_birth=patient_data.date_of_birth,
        gender=patient_data.gender,
        phone=patient_data.phone,
        address=patient_data.address,
        emergency_contact=patient_data.emergency_contact,
        medical_history=patient_in_db.medical_history,
        allergies=patient_in_db.allergies,
        medications=patient_in_db.medications,
        created_at=patient_in_db.created_at,
        updated_at=patient_in_db.updated_at
    )

@router.get("/", response_model=PatientResponse)
async def get_patient(current_user: dict = Depends(get_current_user)):
    """Get patient record for current user"""
    db = require_database()
    
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    return PatientResponse(
        id=str(patient["_id"]),
        patient_id=patient["patient_id"],
        user_id=patient["user_id"],
        first_name=patient["first_name"],
        last_name=patient["last_name"],
        date_of_birth=patient["date_of_birth"],
        gender=patient["gender"],
        phone=patient["phone"],
        address=patient["address"],
        emergency_contact=patient["emergency_contact"],
        medical_history=patient.get("medical_history", []),
        allergies=patient.get("allergies", []),
        medications=patient.get("medications", []),
        created_at=patient["created_at"],
        updated_at=patient["updated_at"]
    )

@router.put("/", response_model=PatientResponse)
async def update_patient(
    patient_update: PatientUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Update patient record"""
    db = require_database()
    
    # Check if patient exists
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    # Update patient data
    update_data = patient_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.patients.update_one(
        {"user_id": current_user["user_id"]},
        {"$set": update_data}
    )
    
    # Get updated patient
    updated_patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    
    return PatientResponse(
        id=str(updated_patient["_id"]),
        patient_id=updated_patient["patient_id"],
        user_id=updated_patient["user_id"],
        first_name=updated_patient["first_name"],
        last_name=updated_patient["last_name"],
        date_of_birth=updated_patient["date_of_birth"],
        gender=updated_patient["gender"],
        phone=updated_patient["phone"],
        address=updated_patient["address"],
        emergency_contact=updated_patient["emergency_contact"],
        medical_history=updated_patient.get("medical_history", []),
        allergies=updated_patient.get("allergies", []),
        medications=updated_patient.get("medications", []),
        created_at=updated_patient["created_at"],
        updated_at=updated_patient["updated_at"]
    )

@router.post("/test-medical-history")
async def test_add_medical_history(
    medical_history: str = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """Test medical history endpoint without patient validation"""
    return {"message": "Test successful", "medical_history": medical_history, "user_id": current_user["user_id"]}

@router.post("/medical-history")
async def add_medical_history(
    request: MedicalHistoryRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add medical history entry"""
    db = require_database()
    
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    if not request.medical_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="medical_history cannot be empty"
        )
    
    await db.patients.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$push": {"medical_history": request.medical_history},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Medical history added successfully"}

@router.post("/allergies")
async def add_allergy(
    request: AllergyRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add allergy information"""
    db = require_database()
    
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    if not request.allergy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="allergy cannot be empty"
        )
    
    await db.patients.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$push": {"allergies": request.allergy},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Allergy added successfully"}

@router.post("/medications")
async def add_medication(
    request: MedicationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add medication information"""
    db = require_database()
    
    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found"
        )
    
    if not request.medication:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="medication cannot be empty"
        )
    
    await db.patients.update_one(
        {"user_id": current_user["user_id"]},
        {
            "$push": {"medications": request.medication},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    return {"message": "Medication added successfully"}
