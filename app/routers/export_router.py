import os
from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.authentication.auth import get_current_user
from app.services.export_service import export_persons, export_attendance
from app.services.audit_service import create_log
from app.utilities.helpers import get_client_ip

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/persons")
async def export_persons_endpoint(
    request: Request,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        return {"error": "Not authenticated"}
    filepath = export_persons(db, category=category)
    create_log(db, user.get("user_id"), "export", "Person", None, f"Exported persons to Excel", get_client_ip(request))
    return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=os.path.basename(filepath))


@router.get("/attendance")
async def export_attendance_endpoint(
    request: Request,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        return {"error": "Not authenticated"}
    filepath = export_attendance(db, date_from=date_from, date_to=date_to)
    create_log(db, user.get("user_id"), "export", "Attendance", None, f"Exported attendance to Excel", get_client_ip(request))
    return FileResponse(filepath, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=os.path.basename(filepath))
