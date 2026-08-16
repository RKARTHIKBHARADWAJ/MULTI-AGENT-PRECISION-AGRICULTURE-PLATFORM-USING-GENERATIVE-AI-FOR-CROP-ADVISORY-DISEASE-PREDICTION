import json
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

import config
from api.deps import get_current_user
from api.schemas import FarmDecision, ReportResponse, ReportRunRequest
from database.models import Alert, Field, Report, User
from database.session import get_db
from orchestrator.orchestrator import Orchestrator

router = APIRouter(prefix="/reports", tags=["reports"])


def _save_upload(image: UploadFile) -> str:
    suffix = Path(image.filename or "leaf.jpg").suffix or ".jpg"
    filename = f"{uuid.uuid4().hex}{suffix}"
    dest = config.UPLOAD_DIR / filename
    dest.write_bytes(image.file.read())
    return str(dest)


def _build_context(
    payload: ReportRunRequest,
    image_path: Optional[str] = None,
) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "crop": payload.crop,
        "growth_stage": payload.growth_stage,
        "latitude": payload.latitude,
        "longitude": payload.longitude,
    }
    if payload.soil_data:
        context["soil_data"] = payload.soil_data.model_dump(exclude_none=True)
    if image_path:
        context["image_path"] = image_path
    return context


def _create_alerts_from_decisions(
    db: Session,
    user_id: int,
    report_id: int,
    decisions: List[Dict[str, Any]],
) -> None:
    for decision in decisions:
        if decision.get("priority") in ("high", "medium"):
            db.add(
                Alert(
                    user_id=user_id,
                    report_id=report_id,
                    priority=decision["priority"],
                    action=decision["action"],
                    reason=decision["reason"],
                )
            )


def _report_to_response(report: Report) -> ReportResponse:
    decisions = json.loads(report.farm_decisions_json or "[]")
    pipeline_result = (
        json.loads(report.pipeline_result_json) if report.pipeline_result_json else None
    )
    return ReportResponse(
        id=report.id,
        crop=report.crop,
        growth_stage=report.growth_stage,
        latitude=report.latitude,
        longitude=report.longitude,
        crop_advisory=report.crop_advisory,
        farm_decisions=[FarmDecision(**d) for d in decisions],
        field_id=report.field_id,
        image_path=report.image_path,
        created_at=report.created_at,
        pipeline_result=pipeline_result,
    )


def _run_and_persist(
    db: Session,
    user: User,
    payload: ReportRunRequest,
    image_path: Optional[str] = None,
) -> Report:
    if payload.field_id:
        field = (
            db.query(Field)
            .filter(Field.id == payload.field_id, Field.user_id == user.id)
            .first()
        )
        if not field:
            raise HTTPException(status_code=404, detail="Field not found")

    context = _build_context(payload, image_path)
    result = Orchestrator().run(context)

    report = Report(
        user_id=user.id,
        field_id=payload.field_id,
        crop=payload.crop,
        growth_stage=payload.growth_stage,
        latitude=payload.latitude,
        longitude=payload.longitude,
        crop_advisory=result.get("crop_advisory"),
        farm_decisions_json=json.dumps(result.get("farm_decisions", [])),
        pipeline_result_json=json.dumps(result, default=str),
        image_path=image_path,
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    _create_alerts_from_decisions(
        db, user.id, report.id, result.get("farm_decisions", [])
    )
    db.commit()
    return report


@router.post("/run", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
def run_report_json(
    payload: ReportRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = _run_and_persist(db, current_user, payload)
    return _report_to_response(report)


@router.post("/run-with-image", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def run_report_with_image(
    crop: str = Form(...),
    growth_stage: str = Form("unspecified"),
    latitude: float = Form(...),
    longitude: float = Form(...),
    field_id: Optional[int] = Form(None),
    moisture_pct: Optional[float] = Form(None),
    ph: Optional[float] = Form(None),
    nitrogen_ppm: Optional[float] = Form(None),
    phosphorus_ppm: Optional[float] = Form(None),
    potassium_ppm: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from api.schemas import SoilDataInput

    soil_data = SoilDataInput(
        moisture_pct=moisture_pct,
        ph=ph,
        nitrogen_ppm=nitrogen_ppm,
        phosphorus_ppm=phosphorus_ppm,
        potassium_ppm=potassium_ppm,
    )
    has_soil = any(v is not None for v in soil_data.model_dump().values())
    payload = ReportRunRequest(
        crop=crop,
        growth_stage=growth_stage,
        latitude=latitude,
        longitude=longitude,
        field_id=field_id,
        soil_data=soil_data if has_soil else None,
    )

    image_path = None
    if image and image.filename:
        image_path = _save_upload(image)

    report = _run_and_persist(db, current_user, payload, image_path)
    return _report_to_response(report)


@router.get("", response_model=list[ReportResponse])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reports = (
        db.query(Report)
        .filter(Report.user_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return [_report_to_response(r) for r in reports]


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = (
        db.query(Report)
        .filter(Report.id == report_id, Report.user_id == current_user.id)
        .first()
    )
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_response(report)
