from datetime import datetime, date, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.models.person import Person
from app.models.attendance import Attendance


def get_dashboard_stats(db: Session) -> Dict[str, Any]:
    today = date.today()

    total_persons = db.query(Person).filter(Person.is_active == True).count()

    men_count = db.query(Person).filter(Person.is_active == True, Person.category == "Men").count()
    women_count = db.query(Person).filter(Person.is_active == True, Person.category == "Women").count()
    stakeholder_count = db.query(Person).filter(Person.is_active == True, Person.category == "Stakeholders").count()

    today_verified = db.query(Attendance).filter(
        cast(Attendance.verification_date, Date) == today,
        Attendance.status == "Verified",
    ).count()

    not_verified = total_persons - today_verified if total_persons > 0 else 0

    weekly_start = today - timedelta(days=today.weekday())
    weekly_count = db.query(Attendance).filter(
        cast(Attendance.verification_date, Date) >= weekly_start,
        Attendance.status == "Verified",
    ).count()

    weekly_percent = round((weekly_count / total_persons * 100), 1) if total_persons > 0 else 0

    return {
        "total_persons": total_persons,
        "men_count": men_count,
        "women_count": women_count,
        "stakeholder_count": stakeholder_count,
        "today_verified": today_verified,
        "not_verified": not_verified,
        "weekly_count": weekly_count,
        "weekly_percent": weekly_percent,
    }


def get_weekly_trend(db: Session) -> list:
    data = []
    today = date.today()
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = db.query(Attendance).filter(
            cast(Attendance.verification_date, Date) == d,
            Attendance.status == "Verified",
        ).count()
        data.append({"date": d.isoformat(), "count": count})
    return data


def get_category_distribution(db: Session) -> list:
    rows = db.query(Person.category, func.count(Person.id)).filter(Person.is_active == True).group_by(Person.category).all()
    return [{"category": r[0] or "Uncategorized", "count": r[1]} for r in rows]


def get_gender_distribution(db: Session) -> list:
    from sqlalchemy import and_
    rows = db.query(Person.gender, func.count(Person.id)).filter(
        Person.is_active == True,
        Person.gender.isnot(None),
        Person.gender != "",
    ).group_by(Person.gender).all()
    return [{"gender": r[0], "count": r[1]} for r in rows]


def get_todays_attendance_by_category(db: Session) -> list:
    today = date.today()
    rows = db.query(Attendance.category, func.count(Attendance.id)).filter(
        cast(Attendance.verification_date, Date) == today,
        Attendance.status == "Verified",
    ).group_by(Attendance.category).all()
    return [{"category": r[0] or "Uncategorized", "count": r[1]} for r in rows]
