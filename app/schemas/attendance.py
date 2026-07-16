from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class AttendanceVerify(BaseModel):
    person_id: int
    person_category: str
    remarks: Optional[str] = None
    override: bool = False


class AttendanceSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    status: Optional[str] = None
    page: int = 1
    page_size: int = 50


class AttendanceResponse(BaseModel):
    id: int
    person_id: int
    person_name: str
    person_category: str
    designation: Optional[str] = None
    region_division: Optional[str] = None
    verification_time: datetime
    verified_by: int
    verified_by_name: Optional[str] = None
    status: str
    remarks: Optional[str] = None
    is_overridden: bool

    model_config = {"from_attributes": True}


class AttendanceStats(BaseModel):
    total_verified: int
    verified_today: int
    men_verified: int
    women_verified: int
    stakeholders_verified: int
    pending_verification: int
