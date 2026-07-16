from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.authentication.auth import get_current_user
from app.services.search_service import global_search

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("")
async def api_search(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
):
    user = get_current_user(request)
    if not user:
        return {"persons": [], "attendance": []}
    results = global_search(db, q)
    return {
        "persons": [
            {
                "id": p.id,
                "name": p.name,
                "gender": p.gender or "",
                "designation": p.designation or "",
                "phone_number": p.phone_number or "",
                "region_division": p.region_division or "",
                "category": p.category or "",
            }
            for p in results["persons"]
        ],
        "attendance": [
            {
                "id": r.id,
                "person_name": r.person_name,
                "designation": r.designation or "",
                "verification_time": r.verification_time.isoformat() if r.verification_time else "",
                "status": r.status,
            }
            for r in results["attendance"]
        ],
    }
