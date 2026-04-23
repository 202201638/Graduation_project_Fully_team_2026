from pydantic import BaseModel, ConfigDict, Field
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Optional, List
from datetime import UTC, datetime
from bson import ObjectId


def utc_now() -> datetime:
    return datetime.now(UTC)

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
    gender: Optional[str] = Field(default=None, pattern="^(male|female|other)$")
    phone: Optional[str] = None
    address: Optional[str] = None
    emergency_contact: Optional[str] = None

class PatientInDB(PatientBase):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    patient_id: str
    user_id: str
    medical_history: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    medications: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

class PatientResponse(PatientBase):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    patient_id: str
    user_id: str
    medical_history: List[str]
    allergies: List[str]
    medications: List[str]
    created_at: datetime
    updated_at: datetime


class PatientSummary(BaseModel):
    id: str
    patient_id: str
    user_id: str
    first_name: str
    last_name: str
    date_of_birth: str
    gender: str
    phone: str
    address: str
    emergency_contact: str
    created_at: datetime
    updated_at: datetime
