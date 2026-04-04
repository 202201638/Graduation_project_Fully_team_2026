from pydantic import BaseModel, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, List
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

class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # Format: YYYY-MM-DD
    gender: str = Field(pattern="^(male|female|other)$")
    phone: str
    address: str
    emergency_contact: str

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # Format: YYYY-MM-DD
    gender: str = Field(pattern="^(male|female|other)$")
    phone: str
    address: str
    emergency_contact: str

class PatientUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class PatientInDB(PatientBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    patient_id: str
    user_id: str
    medical_history: List[str] = []
    allergies: List[str] = []
    medications: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class PatientResponse(PatientBase):
    id: str
    patient_id: str
    user_id: str
    medical_history: List[str]
    allergies: List[str]
    medications: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
