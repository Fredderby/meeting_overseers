from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class PersonBase(BaseModel):
    name: str
    designation: Optional[str] = None
    phone_number: Optional[str] = None
    region_division: Optional[str] = None


class PersonCreate(PersonBase):
    remarks: Optional[str] = None


class PersonUpdate(BaseModel):
    name: Optional[str] = None
    designation: Optional[str] = None
    phone_number: Optional[str] = None
    region_division: Optional[str] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class PersonResponse(PersonBase):
    id: int
    category: str
    verification_status: str
    verification_date: Optional[datetime] = None
    remarks: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BulkAction(BaseModel):
    ids: List[int]
    action: str
    value: Optional[str] = None


class PersonSearch(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    designation: Optional[str] = None
    region: Optional[str] = None
    verification_status: Optional[str] = None
    search_mode: str = "contains"
    page: int = 1
    page_size: int = 50
    sort_by: str = "name"
    sort_order: str = "asc"
