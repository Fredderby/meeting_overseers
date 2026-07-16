from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.person import Person
from app.models.attendance import Attendance


def global_search(db: Session, query: str) -> Dict[str, Any]:
    q = f"%{query}%"
    persons = db.query(Person).filter(
        Person.is_active == True,
        or_(
            Person.name.ilike(q),
            Person.designation.ilike(q),
            Person.phone_number.ilike(q),
            Person.region_division.ilike(q),
            Person.gender.ilike(q),
            Person.remarks.ilike(q),
        ),
    ).order_by(Person.name).all()

    attendance_records = db.query(Attendance).filter(
        or_(
            Attendance.person_name.ilike(q),
            Attendance.designation.ilike(q),
            Attendance.region_division.ilike(q),
        ),
    ).order_by(Attendance.verification_time.desc()).limit(50).all()

    return {"persons": persons, "attendance": attendance_records}
