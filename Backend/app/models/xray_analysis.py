from pydantic import BaseModel, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, Dict, Any
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
    patient_id: str
    image_url: str
    image_filename: str

class XRayAnalysisCreate(XRayAnalysisBase):
    pass

class AnalysisResult(BaseModel):
    pneumonia_detected: bool
    confidence_score: float  # 0.0 to 1.0
    findings: str
    recommendations: str
    analysis_details: Dict[str, Any] = {}

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
    id: str
    analysis_id: str
    patient_id: str
    result: Optional[AnalysisResult] = None
    status: str
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True

class XRayAnalysisSummary(BaseModel):
    analysis_id: str
    patient_id: str
    status: str
    pneumonia_detected: Optional[bool] = None
    confidence_score: Optional[float] = None
    created_at: datetime
