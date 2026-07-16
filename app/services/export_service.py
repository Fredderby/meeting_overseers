import os
import pandas as pd
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.person import Person
from app.models.attendance import Attendance


def export_persons(db: Session, category: Optional[str] = None) -> str:
    query = db.query(Person).filter(Person.is_active == True)
    if category:
        query = query.filter(Person.category == category)
    persons = query.order_by(Person.name).all()

    data = []
    for p in persons:
        data.append({
            "ID": p.id,
            "Name": p.name,
            "Gender": p.gender or "",
            "Designation": p.designation or "",
            "Phone Number": p.phone_number or "",
            "Region/Division": p.region_division or "",
            "Category": p.category or "",
            "Remarks": p.remarks or "",
        })

    df = pd.DataFrame(data)
    os.makedirs(settings.EXPORT_FOLDER, exist_ok=True)
    filename = f"persons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(settings.EXPORT_FOLDER, filename)
    df.to_excel(filepath, index=False)
    return filepath


def export_attendance(db: Session, date_from: Optional[str] = None, date_to: Optional[str] = None) -> str:
    query = db.query(Attendance)
    if date_from:
        query = query.filter(Attendance.verification_date >= datetime.strptime(date_from, "%Y-%m-%d"))
    if date_to:
        query = query.filter(Attendance.verification_date <= datetime.strptime(date_to, "%Y-%m-%d") + pd.Timedelta(days=1))
    records = query.order_by(Attendance.verification_time.desc()).all()

    data = []
    for r in records:
        data.append({
            "ID": r.id,
            "Person ID": r.person_id,
            "Name": r.person_name,
            "Gender": r.gender or "",
            "Designation": r.designation or "",
            "Region/Division": r.region_division or "",
            "Category": r.category or "",
            "Verification Time": r.verification_time.strftime("%Y-%m-%d %H:%M:%S") if r.verification_time else "",
            "Verified By": r.verified_by_name or "",
            "Status": r.status,
        })

    df = pd.DataFrame(data)
    os.makedirs(settings.EXPORT_FOLDER, exist_ok=True)
    filename = f"attendance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(settings.EXPORT_FOLDER, filename)
    df.to_excel(filepath, index=False)
    return filepath
