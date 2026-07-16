from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class StatCard(BaseModel):
    label: str
    value: int
    icon: str
    color: str
    trend: Optional[str] = None


class DashboardData(BaseModel):
    stats: List[StatCard]
    verification_trend: List[Dict[str, Any]]
    category_breakdown: List[Dict[str, Any]]
    designation_breakdown: List[Dict[str, Any]]
    region_breakdown: List[Dict[str, Any]]
    recent_verifications: List[Dict[str, Any]]
    pending_by_region: List[Dict[str, Any]]
    pending_by_category: List[Dict[str, Any]]
