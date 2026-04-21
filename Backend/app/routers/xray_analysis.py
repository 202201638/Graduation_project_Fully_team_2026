from pathlib import Path
from typing import List, Optional
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.concurrency import run_in_threadpool

from app.database.mongodb import require_database
from app.models.xray_analysis import (
    AnalysisResult,
    MetadataSummaryResponse,
    ModelStatusResponse,
    WebXRayAnalysisResponse,
    XRayAnalysisResponse,
    XRayAnalysisSummary,
)
from app.utils.security import verify_token
from app.utils.xray_inference import SavedUpload, xray_inference_service

router = APIRouter()
security = HTTPBearer()
BACKEND_DIR = Path(__file__).resolve().parents[2]
DIAGNOSIS_STATUS_CONFIRMED = "pneumonia_detected"
DIAGNOSIS_STATUS_SUSPECTED = "suspected_pneumonia"
DIAGNOSIS_STATUS_CLEAR = "no_pneumonia_detected"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current user from token"""
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


def _metadata_or_404(key: str, label: str):
    payload = xray_inference_service.get_raw_metadata(key)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{label} metadata is not available.",
        )
    return payload


def _cleanup_saved_upload(saved_upload: Optional[SavedUpload]) -> None:
    if saved_upload and saved_upload.file_path.exists():
        saved_upload.file_path.unlink(missing_ok=True)


def _cleanup_image_url(image_url: Optional[str]) -> None:
    if not image_url:
        return

    relative_path = image_url.lstrip("/")
    target_path = BACKEND_DIR / relative_path
    if target_path.exists():
        target_path.unlink(missing_ok=True)


def _resolve_diagnosis_status(result: Optional[dict]) -> str:
    if not isinstance(result, dict):
        return DIAGNOSIS_STATUS_CLEAR

    diagnosis_status = result.get("diagnosis_status")
    if diagnosis_status in {
        DIAGNOSIS_STATUS_CONFIRMED,
        DIAGNOSIS_STATUS_SUSPECTED,
        DIAGNOSIS_STATUS_CLEAR,
    }:
        return diagnosis_status

    if result.get("suspected_pneumonia") is True:
        return DIAGNOSIS_STATUS_SUSPECTED

    if result.get("pneumonia_detected") is True:
        return DIAGNOSIS_STATUS_CONFIRMED

    return DIAGNOSIS_STATUS_CLEAR


def _normalize_result_payload(result: Optional[dict]) -> Optional[dict]:
    if not isinstance(result, dict):
        return result

    normalized_result = dict(result)
    diagnosis_status = _resolve_diagnosis_status(normalized_result)
    normalized_result.setdefault("diagnosis_status", diagnosis_status)
    normalized_result.setdefault(
        "suspected_pneumonia",
        diagnosis_status == DIAGNOSIS_STATUS_SUSPECTED,
    )
    return normalized_result


def _resolve_analysis_model_details(analysis: dict) -> tuple[Optional[str], Optional[str], Optional[str]]:
    model_name = analysis.get("model_name")
    model_display_name = analysis.get("model_display_name")
    model_family = analysis.get("model_family")

    result = analysis.get("result")
    if isinstance(result, dict):
        result = _normalize_result_payload(result) or {}
        analysis_details = result.get("analysis_details")
        if isinstance(analysis_details, dict):
            model_name = model_name or analysis_details.get("model_name")
            model_display_name = model_display_name or analysis_details.get("model_display_name")
            model_family = model_family or analysis_details.get("model_family")

    return model_name, model_display_name, model_family


async def _save_upload(file: UploadFile) -> SavedUpload:
    contents = await file.read()

    try:
        return xray_inference_service.validate_and_save_upload(
            filename=file.filename or "",
            contents=contents,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


async def _run_inference(
    saved_upload: SavedUpload,
    patient_id: Optional[str] = None,
    scan_type: Optional[str] = None,
    model_name: Optional[str] = None,
):
    try:
        return await run_in_threadpool(
            xray_inference_service.predict,
            saved_upload,
            patient_id,
            scan_type,
            model_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {exc}",
        ) from exc


@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify router is working"""
    return {"message": "X-ray analysis router is working", "status": "ok"}


@router.get("/status", response_model=ModelStatusResponse)
async def get_model_status():
    """Return model runtime status"""
    return xray_inference_service.get_status()


@router.get("/metadata", response_model=MetadataSummaryResponse)
async def get_metadata_summary():
    """Return summarized metadata for the deployed model assets"""
    return xray_inference_service.get_metadata_summary()


@router.get("/metadata/manifest")
async def get_manifest_metadata():
    """Return raw manifest metadata"""
    return _metadata_or_404("manifest", "Manifest")


@router.get("/metadata/baseline")
async def get_baseline_metadata():
    """Return raw baseline evaluation metadata"""
    return _metadata_or_404("baseline", "Baseline")


@router.get("/metadata/web-result")
async def get_web_result_metadata():
    """Return raw web result metadata"""
    return _metadata_or_404("web_result", "Web result")


@router.get("/metadata/demo-result")
async def get_demo_result_metadata():
    """Return raw optional demo result metadata"""
    return _metadata_or_404("demo_result", "Demo result")


@router.post("/analyze", response_model=WebXRayAnalysisResponse)
async def analyze_xray_for_web(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    scan_type: Optional[str] = Form(None),
    selected_model_name: Optional[str] = Form(None, alias="model_name"),
):
    """Upload and analyze an X-ray image without authentication"""
    saved_upload: Optional[SavedUpload] = None

    try:
        saved_upload = await _save_upload(file)
        return await _run_inference(saved_upload, patient_id, scan_type, selected_model_name)
    except HTTPException:
        _cleanup_saved_upload(saved_upload)
        raise


@router.post("/upload", response_model=XRayAnalysisResponse)
async def upload_xray(
    file: UploadFile = File(...),
    patient_id: Optional[str] = Form(None),
    selected_model_name: Optional[str] = Form(None, alias="model_name"),
    current_user: dict = Depends(get_current_user),
):
    """Upload and analyze X-ray image for an authenticated patient"""
    db = require_database()
    saved_upload: Optional[SavedUpload] = None
    inserted_analysis_id = None

    if patient_id:
        patient = await db.patients.find_one(
            {"patient_id": patient_id, "user_id": current_user["user_id"]}
        )
    else:
        patient = await db.patients.find_one({"user_id": current_user["user_id"]})

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found. Please create a patient record first or provide a valid patient_id.",
        )

    try:
        saved_upload = await _save_upload(file)
        analysis_in_db = {
            "analysis_id": None,
            "patient_id": patient["patient_id"],
            "image_url": saved_upload.image_url,
            "image_filename": saved_upload.original_filename,
            "status": "processing",
            "created_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        analysis_result = await _run_inference(
            saved_upload,
            patient["patient_id"],
            None,
            selected_model_name,
        )
        analysis_in_db["analysis_id"] = analysis_result["analysis_id"]
        analysis_in_db["model_name"] = analysis_result.get("model_name")
        analysis_in_db["model_display_name"] = analysis_result.get("model_display_name")
        analysis_in_db["model_family"] = analysis_result.get("model_family")

        insert_result = await db.xray_analyses.insert_one(analysis_in_db)
        inserted_analysis_id = insert_result.inserted_id

        await db.xray_analyses.update_one(
            {"_id": inserted_analysis_id},
            {
                "$set": {
                    "result": analysis_result["result"],
                    "model_name": analysis_result.get("model_name"),
                    "model_display_name": analysis_result.get("model_display_name"),
                    "model_family": analysis_result.get("model_family"),
                    "status": "completed",
                    "processing_time": analysis_result["processing_time"],
                    "updated_at": analysis_result["created_at"],
                }
            },
        )

        updated_analysis = await db.xray_analyses.find_one({"_id": inserted_analysis_id})

        return XRayAnalysisResponse(
            id=str(updated_analysis["_id"]),
            analysis_id=updated_analysis["analysis_id"],
            patient_id=updated_analysis["patient_id"],
            model_name=updated_analysis.get("model_name"),
            model_display_name=updated_analysis.get("model_display_name"),
            model_family=updated_analysis.get("model_family"),
            image_url=updated_analysis["image_url"],
            image_filename=updated_analysis["image_filename"],
            result=AnalysisResult(**_normalize_result_payload(updated_analysis["result"])),
            status=updated_analysis["status"],
            processing_time=updated_analysis["processing_time"],
            created_at=updated_analysis["created_at"],
            updated_at=updated_analysis["updated_at"],
        )

    except HTTPException as exc:
        if inserted_analysis_id is not None:
            await db.xray_analyses.update_one(
                {"_id": inserted_analysis_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": exc.detail,
                        "updated_at": datetime.now(UTC),
                    }
                },
            )
        else:
            _cleanup_saved_upload(saved_upload)
        raise
    except Exception as exc:
        if inserted_analysis_id is not None:
            await db.xray_analyses.update_one(
                {"_id": inserted_analysis_id},
                {
                    "$set": {
                        "status": "failed",
                        "error_message": str(exc),
                        "updated_at": datetime.now(UTC),
                    }
                },
            )
        else:
            _cleanup_saved_upload(saved_upload)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload and analysis failed: {exc}",
        ) from exc


@router.get("/", response_model=List[XRayAnalysisSummary])
async def get_analyses(current_user: dict = Depends(get_current_user)):
    """Get all X-ray analyses for current user"""
    db = require_database()

    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found",
        )

    analyses = (
        await db.xray_analyses.find({"patient_id": patient["patient_id"]})
        .sort("created_at", -1)
        .to_list(length=None)
    )

    summaries = []
    for analysis in analyses:
        result = _normalize_result_payload(analysis.get("result", {})) or {}
        model_name, model_display_name, model_family = _resolve_analysis_model_details(analysis)
        summaries.append(
            XRayAnalysisSummary(
                analysis_id=analysis["analysis_id"],
                patient_id=analysis["patient_id"],
                status=analysis["status"],
                model_name=model_name,
                model_display_name=model_display_name,
                model_family=model_family,
                pneumonia_detected=result.get("pneumonia_detected"),
                suspected_pneumonia=result.get("suspected_pneumonia"),
                diagnosis_status=result.get("diagnosis_status"),
                confidence_score=result.get("confidence_score"),
                created_at=analysis["created_at"],
            )
        )

    return summaries


@router.get("/{analysis_id}", response_model=XRayAnalysisResponse)
async def get_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Get specific X-ray analysis"""
    db = require_database()

    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found",
        )

    analysis = await db.xray_analyses.find_one(
        {
            "analysis_id": analysis_id,
            "patient_id": patient["patient_id"],
        }
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    result_data = _normalize_result_payload(analysis.get("result"))
    result = AnalysisResult(**result_data) if result_data else None
    model_name, model_display_name, model_family = _resolve_analysis_model_details(analysis)

    return XRayAnalysisResponse(
        id=str(analysis["_id"]),
        analysis_id=analysis["analysis_id"],
        patient_id=analysis["patient_id"],
        model_name=model_name,
        model_display_name=model_display_name,
        model_family=model_family,
        image_url=analysis["image_url"],
        image_filename=analysis["image_filename"],
        result=result,
        status=analysis["status"],
        error_message=analysis.get("error_message"),
        processing_time=analysis.get("processing_time"),
        created_at=analysis["created_at"],
        updated_at=analysis["updated_at"],
    )


@router.delete("/{analysis_id}")
async def delete_analysis(
    analysis_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete X-ray analysis"""
    db = require_database()

    patient = await db.patients.find_one({"user_id": current_user["user_id"]})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient record not found",
        )

    analysis = await db.xray_analyses.find_one(
        {
            "analysis_id": analysis_id,
            "patient_id": patient["patient_id"],
        }
    )

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    _cleanup_image_url(analysis.get("image_url"))

    result_data = analysis.get("result") or {}
    _cleanup_image_url(result_data.get("rendered_image_url"))

    await db.xray_analyses.delete_one({"_id": analysis["_id"]})
    return {"message": "Analysis deleted successfully"}
