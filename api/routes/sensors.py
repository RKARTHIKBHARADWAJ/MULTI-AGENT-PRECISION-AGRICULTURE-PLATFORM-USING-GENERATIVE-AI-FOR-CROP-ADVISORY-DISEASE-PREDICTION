from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.schemas import SensorReadingCreate, SensorReadingResponse
from database.models import Field, SensorReading, User
from database.session import get_db

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("/readings", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED)
def create_sensor_reading(
    payload: SensorReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    field = (
        db.query(Field)
        .filter(Field.id == payload.field_id, Field.user_id == current_user.id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    reading = SensorReading(
        field_id=payload.field_id,
        moisture_pct=payload.moisture_pct,
        ph=payload.ph,
        nitrogen_ppm=payload.nitrogen_ppm,
        phosphorus_ppm=payload.phosphorus_ppm,
        potassium_ppm=payload.potassium_ppm,
        source=payload.source,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("/readings/{field_id}", response_model=list[SensorReadingResponse])
def list_sensor_readings(
    field_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    field = (
        db.query(Field)
        .filter(Field.id == field_id, Field.user_id == current_user.id)
        .first()
    )
    if not field:
        raise HTTPException(status_code=404, detail="Field not found")

    return (
        db.query(SensorReading)
        .filter(SensorReading.field_id == field_id)
        .order_by(SensorReading.created_at.desc())
        .limit(50)
        .all()
    )
