from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FieldCreate(BaseModel):
    name: str
    crop: str
    growth_stage: str = "unspecified"
    latitude: float
    longitude: float


class FieldResponse(BaseModel):
    id: int
    name: str
    crop: str
    growth_stage: str
    latitude: float
    longitude: float
    created_at: datetime

    class Config:
        from_attributes = True


class SoilDataInput(BaseModel):
    moisture_pct: Optional[float] = None
    ph: Optional[float] = None
    nitrogen_ppm: Optional[float] = None
    phosphorus_ppm: Optional[float] = None
    potassium_ppm: Optional[float] = None


class ReportRunRequest(BaseModel):
    crop: str
    growth_stage: str = "unspecified"
    latitude: float
    longitude: float
    field_id: Optional[int] = None
    soil_data: Optional[SoilDataInput] = None


class FarmDecision(BaseModel):
    action: str
    priority: str
    reason: str


class ReportResponse(BaseModel):
    id: int
    crop: str
    growth_stage: str
    latitude: float
    longitude: float
    crop_advisory: Optional[str]
    farm_decisions: List[FarmDecision]
    field_id: Optional[int]
    image_path: Optional[str]
    created_at: datetime
    pipeline_result: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    id: int
    report_id: Optional[int]
    priority: str
    action: str
    reason: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class SensorReadingCreate(BaseModel):
    field_id: int
    moisture_pct: Optional[float] = None
    ph: Optional[float] = None
    nitrogen_ppm: Optional[float] = None
    phosphorus_ppm: Optional[float] = None
    potassium_ppm: Optional[float] = None
    source: str = "manual"


class SensorReadingResponse(BaseModel):
    id: int
    field_id: int
    moisture_pct: Optional[float]
    ph: Optional[float]
    nitrogen_ppm: Optional[float]
    phosphorus_ppm: Optional[float]
    potassium_ppm: Optional[float]
    source: str
    created_at: datetime

    class Config:
        from_attributes = True
