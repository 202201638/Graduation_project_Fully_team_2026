from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: JsonSchemaValue) -> JsonSchemaValue:
        return {"type": "string"}
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.no_info_plain_validator_function(cls.validate)
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class XRayAnalysisBase(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    patient_id: str
    image_url: str
    image_filename: str

class XRayAnalysisCreate(XRayAnalysisBase):
    pass

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

class DetectionPrediction(BaseModel):
    label: str
    class_id: int
    confidence: float
    bbox: BoundingBox

DiagnosisStatus = Literal[
    "pneumonia_detected",
    "suspected_pneumonia",
    "no_pneumonia_detected",
]

class AnalysisResult(BaseModel):
    pneumonia_detected: bool
    suspected_pneumonia: bool = False
    diagnosis_status: DiagnosisStatus = "no_pneumonia_detected"
    confidence_score: float  # 0.0 to 1.0
    findings: str
    recommendations: str
    analysis_details: Dict[str, Any] = Field(default_factory=dict)
    detections: List[DetectionPrediction] = Field(default_factory=list)
    original_image_url: Optional[str] = None
    rendered_image_url: Optional[str] = None

class XRayAnalysisInDB(XRayAnalysisBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    analysis_id: str
    patient_id: str
    result: Optional[AnalysisResult] = None
    status: str = Field(default="pending", pattern="^(pending|processing|completed|failed)$")
    error_message: Optional[str] = None
    processing_time: Optional[float] = None  # in seconds
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class XRayAnalysisResponse(XRayAnalysisBase):
    model_config = ConfigDict(
        populate_by_name=True,
        protected_namespaces=(),
    )

    id: str
    analysis_id: str
    patient_id: str
    model_name: Optional[str] = None
    model_display_name: Optional[str] = None
    model_family: Optional[str] = None
    result: Optional[AnalysisResult] = None
    status: str
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class XRayAnalysisSummary(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    analysis_id: str
    patient_id: str
    status: str
    model_name: Optional[str] = None
    model_display_name: Optional[str] = None
    model_family: Optional[str] = None
    pneumonia_detected: Optional[bool] = None
    suspected_pneumonia: Optional[bool] = None
    diagnosis_status: Optional[DiagnosisStatus] = None
    confidence_score: Optional[float] = None
    created_at: datetime

class AvailableModelResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    key: str
    display_name: str
    model_family: str
    model_type: str
    task: str
    weights_file: str
    available: bool
    loaded: bool = False
    class_names: List[str] = Field(default_factory=list)
    default_conf: Optional[float] = None
    confirmed_conf: Optional[float] = None
    default_imgsz: Optional[int] = None
    input_size: Optional[int] = None
    description: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)
    primary_metric_label: Optional[str] = None
    primary_metric_value: Optional[float] = None
    secondary_metric_label: Optional[str] = None
    secondary_metric_value: Optional[float] = None
    load_error: Optional[str] = None

class ModelStatusResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    status: str
    model_loaded: bool
    weights_file: str
    weights_exists: bool
    model_type: Optional[str] = None
    task: Optional[str] = None
    class_names: List[str] = Field(default_factory=list)
    default_conf: Optional[float] = None
    confirmed_conf: Optional[float] = None
    default_imgsz: Optional[int] = None
    default_model_key: Optional[str] = None
    display_name: Optional[str] = None
    model_family: Optional[str] = None
    available_models: List[AvailableModelResponse] = Field(default_factory=list)
    metadata_available: Dict[str, bool] = Field(default_factory=dict)
    load_error: Optional[str] = None

class MetadataSummaryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    manifest: Dict[str, Any] = Field(default_factory=dict)
    baseline: Dict[str, Any] = Field(default_factory=dict)
    web_result: Dict[str, Any] = Field(default_factory=dict)
    demo_result: Optional[Dict[str, Any]] = None
    available_models: List[AvailableModelResponse] = Field(default_factory=list)
    default_model_key: Optional[str] = None

class WebXRayAnalysisResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    analysis_id: str
    patient_id: Optional[str] = None
    scan_type: Optional[str] = None
    model_name: Optional[str] = None
    model_display_name: Optional[str] = None
    model_family: Optional[str] = None
    image_filename: str
    result: AnalysisResult
    status: str
    processing_time: float
    created_at: datetime
