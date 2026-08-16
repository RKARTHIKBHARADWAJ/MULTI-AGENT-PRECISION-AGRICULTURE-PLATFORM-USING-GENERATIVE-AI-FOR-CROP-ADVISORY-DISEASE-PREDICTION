from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user
from api.schemas import FieldCreate, FieldResponse
from database.models import Field, User
from database.session import get_db

router = APIRouter(prefix="/fields", tags=["fields"])


@router.post("", response_model=FieldResponse, status_code=status.HTTP_201_CREATED)
def create_field(
    payload: FieldCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    field = Field(
        user_id=current_user.id,
        name=payload.name,
        crop=payload.crop,
        growth_stage=payload.growth_stage,
        latitude=payload.latitude,
        longitude=payload.longitude,
    )
    db.add(field)
    db.commit()
    db.refresh(field)
    return field


@router.get("", response_model=list[FieldResponse])
def list_fields(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Field)
        .filter(Field.user_id == current_user.id)
        .order_by(Field.created_at.desc())
        .all()
    )


@router.get("/{field_id}", response_model=FieldResponse)
def get_field(
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
    return field
