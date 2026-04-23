from datetime import UTC, datetime
from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.database.mongodb import require_database
from app.models.patient import PatientCreate, PatientInDB, PatientResponse, PatientSummary, PatientUpdate
from app.utils.security import generate_patient_id, verify_token


class MedicalHistoryRequest(BaseModel):
    medical_history: str


class AllergyRequest(BaseModel):
    allergy: str


class MedicationRequest(BaseModel):
    medication: str


router = APIRouter()
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return {
        "user_id": user_id,
        "email": payload.get("email"),
        "role": payload.get("role"),
    }


def _patient_response(patient: dict) -> PatientResponse:
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
        updated_at=patient["updated_at"],
    )


def _patient_summary(patient: dict) -> PatientSummary:
    return PatientSummary(
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
        created_at=patient["created_at"],
        updated_at=patient["updated_at"],
    )


async def _get_owned_patient_or_404(db, patient_id: str, user_id: str) -> dict:
    patient = await db.patients.find_one({"patient_id": patient_id, "user_id": user_id})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found",
        )
    return patient


async def _get_first_patient_or_404(db, user_id: str) -> dict:
    patient = await db.patients.find_one({"user_id": user_id})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found",
        )
    return patient


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient_data: PatientCreate,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()

    user = await db.users.find_one({"user_id": current_user["user_id"]})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

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
        user_id=current_user["user_id"],
    )

    patient_dict = patient_in_db.model_dump(by_alias=True)
    result = await db.patients.insert_one(patient_dict)
    patient_dict["_id"] = result.inserted_id
    return _patient_response(patient_dict)


@router.get("/list", response_model=List[PatientSummary])
async def list_patients(current_user: dict = Depends(get_current_user)):
    db = require_database()
    patients = (
        await db.patients.find({"user_id": current_user["user_id"]})
        .sort("created_at", -1)
        .to_list(length=None)
    )
    return [_patient_summary(patient) for patient in patients]


@router.get("/", response_model=PatientResponse)
async def get_patient(current_user: dict = Depends(get_current_user)):
    db = require_database()
    patient = await _get_first_patient_or_404(db, current_user["user_id"])
    return _patient_response(patient)


@router.put("/", response_model=PatientResponse)
async def update_patient(
    patient_update: PatientUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    patient = await _get_first_patient_or_404(db, current_user["user_id"])
    return await update_patient_by_id(patient["patient_id"], patient_update, current_user)


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient_by_id(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    patient = await _get_owned_patient_or_404(db, patient_id, current_user["user_id"])
    return _patient_response(patient)


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient_by_id(
    patient_id: str,
    patient_update: PatientUpdate,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    await _get_owned_patient_or_404(db, patient_id, current_user["user_id"])

    update_data = patient_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.now(UTC)

    await db.patients.update_one(
        {"patient_id": patient_id, "user_id": current_user["user_id"]},
        {"$set": update_data},
    )

    updated_patient = await _get_owned_patient_or_404(db, patient_id, current_user["user_id"])
    return _patient_response(updated_patient)


@router.delete("/{patient_id}")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    patient = await _get_owned_patient_or_404(db, patient_id, current_user["user_id"])

    analyses = await db.xray_analyses.find({"patient_id": patient["patient_id"]}).to_list(length=None)
    if analyses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient has analysis history. Delete analyses before deleting the patient record.",
        )

    await db.patients.delete_one({"_id": patient["_id"]})
    return {"message": "Patient record deleted successfully"}


@router.post("/test-medical-history")
async def test_add_medical_history(
    medical_history: str = Body(...),
    current_user: dict = Depends(get_current_user),
):
    return {
        "message": "Test successful",
        "medical_history": medical_history,
        "user_id": current_user["user_id"],
    }


@router.post("/medical-history")
async def add_medical_history(
    request: MedicalHistoryRequest,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    patient = await _get_first_patient_or_404(db, current_user["user_id"])
    return await add_medical_history_by_patient(patient["patient_id"], request, current_user)


@router.post("/{patient_id}/medical-history")
async def add_medical_history_by_patient(
    patient_id: str,
    request: MedicalHistoryRequest,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    await _get_owned_patient_or_404(db, patient_id, current_user["user_id"])

    medical_history = request.medical_history.strip()
    if not medical_history:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="medical_history cannot be empty",
        )

    await db.patients.update_one(
        {"patient_id": patient_id, "user_id": current_user["user_id"]},
        {
            "$push": {"medical_history": medical_history},
            "$set": {"updated_at": datetime.now(UTC)},
        },
    )

    return {"message": "Medical history added successfully"}


@router.post("/allergies")
async def add_allergy(
    request: AllergyRequest,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    patient = await _get_first_patient_or_404(db, current_user["user_id"])
    return await add_allergy_by_patient(patient["patient_id"], request, current_user)


@router.post("/{patient_id}/allergies")
async def add_allergy_by_patient(
    patient_id: str,
    request: AllergyRequest,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    await _get_owned_patient_or_404(db, patient_id, current_user["user_id"])

    allergy = request.allergy.strip()
    if not allergy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="allergy cannot be empty",
        )

    await db.patients.update_one(
        {"patient_id": patient_id, "user_id": current_user["user_id"]},
        {
            "$push": {"allergies": allergy},
            "$set": {"updated_at": datetime.now(UTC)},
        },
    )

    return {"message": "Allergy added successfully"}


@router.post("/medications")
async def add_medication(
    request: MedicationRequest,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    patient = await _get_first_patient_or_404(db, current_user["user_id"])
    return await add_medication_by_patient(patient["patient_id"], request, current_user)


@router.post("/{patient_id}/medications")
async def add_medication_by_patient(
    patient_id: str,
    request: MedicationRequest,
    current_user: dict = Depends(get_current_user),
):
    db = require_database()
    await _get_owned_patient_or_404(db, patient_id, current_user["user_id"])

    medication = request.medication.strip()
    if not medication:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="medication cannot be empty",
        )

    await db.patients.update_one(
        {"patient_id": patient_id, "user_id": current_user["user_id"]},
        {
            "$push": {"medications": medication},
            "$set": {"updated_at": datetime.now(UTC)},
        },
    )

    return {"message": "Medication added successfully"}
