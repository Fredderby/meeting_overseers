from typing import List, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Date

from app.models.attendance import Attendance
from app.models.person import Person


def verify_attendance(
    db: Session,
    person_id: int,
    verified_by: int,
    verified_by_name: Optional[str] = None,
    remarks: Optional[str] = None,
) -> Attendance:
    person = db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()
    if not person:
        raise ValueError(f"Person with id {person_id} not found")

    today = date.today()
    existing = db.query(Attendance).filter(
        Attendance.person_id == person_id,
        cast(Attendance.verification_date, Date) == today,
        Attendance.status == "Verified",
    ).first()
    if existing:
        raise ValueError(f"{person.name} has already been verified today")

    att = Attendance(
        person_id=person.id,
        person_name=person.name,
        gender=person.gender,
        designation=person.designation,
        region_division=person.region_division,
        category=person.category,
        verification_time=datetime.utcnow(),
        verification_date=datetime.utcnow(),
        verified_by=verified_by,
        verified_by_name=verified_by_name,
        status="Verified",
        remarks=remarks,
    )
    db.add(att)
    db.commit()
    db.refresh(att)
    return att


def get_today_attendance(
    db: Session,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 200,
) -> Tuple[List[Attendance], int]:
    today = date.today()
    query = db.query(Attendance).filter(cast(Attendance.verification_date, Date) == today)
    if category:
        query = query.filter(Attendance.category == category)
    total = query.count()
    records = query.order_by(Attendance.verification_time.desc()).offset(skip).limit(limit).all()
    return records, total


def get_unverified_persons(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Person]:
    today = date.today()
    verified_ids = db.query(Attendance.person_id).filter(
        cast(Attendance.verification_date, Date) == today,
        Attendance.status == "Verified",
    ).subquery()
    query = db.query(Person).filter(
        Person.is_active == True,
        ~Person.id.in_(verified_ids),
    )
    if category:
        query = query.filter(Person.category == category)
    if search:
        q = f"%{search}%"
        query = query.filter(Person.name.ilike(q))
    return query.order_by(Person.name).all()


def get_attendance_history(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
) -> Tuple[List[Attendance], int]:
    query = db.query(Attendance)
    if category:
        query = query.filter(Attendance.category == category)
    if date_from:
        query = query.filter(cast(Attendance.verification_date, Date) >= date_from)
    if date_to:
        query = query.filter(cast(Attendance.verification_date, Date) <= date_to)
    total = query.count()
    records = query.order_by(Attendance.verification_time.desc()).offset(skip).limit(limit).all()
    return records, total
