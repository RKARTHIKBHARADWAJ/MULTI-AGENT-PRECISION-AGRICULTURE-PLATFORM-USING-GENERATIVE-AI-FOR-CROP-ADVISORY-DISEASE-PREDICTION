import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import config
from api.auth import authenticate_user, create_access_token, create_user, get_user_by_email
from api.deps import get_current_user
from api.schemas import (
    AlertResponse,
    FieldCreate,
    FieldResponse,
    ReportResponse,
    ReportRunRequest,
    SensorReadingCreate,
    SensorReadingResponse,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from database.models import Alert, Field, Report, SensorReading, User
from database.session import get_db
from orchestrator.orchestrator import Orchestrator

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    return create_user(db, payload.email, payload.password, payload.full_name)


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user
