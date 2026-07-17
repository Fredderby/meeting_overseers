from datetime import datetime, date, timedelta
from typing import Dict, Any
import numpy as np
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


def _normalize_designation(desig, category=None):
    if not desig:
        return "Other"
    d = desig.lower().strip()

    if "national" in d or "nat'l" in d:
        return "National Officers"

    cleaned = d
    for prefix in ["former ag.", "former"]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    if cleaned.startswith("ag."):
        cleaned = cleaned[3:].strip()

    if "zonal" in cleaned and "overseer" in cleaned and "women" not in cleaned:
        return "Zonal Coordinating Overseer"
    if "zonal" in cleaned and "coordinat" in cleaned and "overseer" in cleaned:
        return "Zonal Coordinating Overseer"
    if "zonal" in cleaned and "women" in cleaned:
        return "Zonal Women Coordinator"
    if "zonal" in cleaned and "administrator" in cleaned:
        return "Zonal Coordinating Overseer"
    if "regional" in cleaned and "women" in cleaned:
        return "Regional Women Coordinator"
    if "regional" in cleaned and ("overseer" in cleaned or "administrator" in cleaned):
        return "Regional Overseer"
    if "divisional" in cleaned and "women" in cleaned:
        return "Divisional Women Coordinator"
    if "divisional" in cleaned and "pastor" in cleaned:
        return "Divisional Pastor"
    if "group" in cleaned and "women" in cleaned:
        return "Divisional Women Coordinator"
    if "group" in cleaned and "pastor" in cleaned:
        return "Divisional Pastor"
    if category and category.lower() == "women":
        return "Sisters"

    return "Other"


def get_designation_analytics(db: Session) -> dict:
    total = db.query(func.count(Person.id)).filter(Person.is_active == True).scalar() or 0
    today = date.today()
    weekly_start = today - timedelta(days=today.weekday())

    gender_rows = db.query(
        Person.designation, Person.gender, Person.category, func.count(Person.id)
    ).filter(Person.is_active == True).group_by(Person.designation, Person.gender, Person.category).all()
    gender_map = {}
    for desig, gender, category, count in gender_rows:
        key = _normalize_designation(desig, category)
        if key not in gender_map:
            gender_map[key] = {}
        gender_map[key][gender or "Unspecified"] = gender_map[key].get(gender or "Unspecified", 0) + count

    cat_rows = db.query(
        Person.designation, Person.category, func.count(Person.id)
    ).filter(Person.is_active == True).group_by(Person.designation, Person.category).all()
    cat_map = {}
    for desig, cat, count in cat_rows:
        key = _normalize_designation(desig, cat)
        if key not in cat_map:
            cat_map[key] = {}
        cat_map[key][cat or "Uncategorized"] = cat_map[key].get(cat or "Uncategorized", 0) + count

    today_raw = db.query(
        Person.designation, Person.category, func.count(Attendance.id)
    ).join(Person, Attendance.person_id == Person.id).filter(
        cast(Attendance.verification_date, Date) == today,
        Attendance.status == "Verified",
    ).group_by(Person.designation, Person.category).all()
    today_map = {}
    for desig, category, count in today_raw:
        key = _normalize_designation(desig, category)
        today_map[key] = today_map.get(key, 0) + count

    week_raw = db.query(
        Person.designation, Person.category, func.count(Attendance.id)
    ).join(Person, Attendance.person_id == Person.id).filter(
        cast(Attendance.verification_date, Date) >= weekly_start,
        Attendance.status == "Verified",
    ).group_by(Person.designation, Person.category).all()
    week_map = {}
    for desig, category, count in week_raw:
        key = _normalize_designation(desig, category)
        week_map[key] = week_map.get(key, 0) + count

    count_rows = db.query(
        Person.designation, Person.category, func.count(Person.id)
    ).filter(Person.is_active == True).group_by(Person.designation, Person.category).all()

    desig_totals = {}
    for desig, category, count in count_rows:
        key = _normalize_designation(desig, category)
        desig_totals[key] = desig_totals.get(key, 0) + count

    designations = []
    for desig_name, count in desig_totals.items():
        gm = gender_map.get(desig_name, {})
        verified_today = today_map.get(desig_name, 0)
        verified_week = week_map.get(desig_name, 0)
        pct = round(count / total * 100, 1) if total > 0 else 0
        att_rate = round(verified_today / count * 100, 1) if count > 0 else 0

        designations.append({
            "designation": desig_name,
            "total": count,
            "percentage": pct,
            "gender": gm,
            "category": cat_map.get(desig_name, {}),
            "verified_today": verified_today,
            "verified_week": verified_week,
            "attendance_rate": att_rate,
        })

    designations.sort(key=lambda x: x["total"], reverse=True)

    chart_data = [{"designation": d["designation"], "count": d["total"]} for d in designations]
    gender_chart = []
    for d in designations:
        male = d["gender"].get("Male", 0)
        female = d["gender"].get("Female", 0)
        other = sum(v for k, v in d["gender"].items() if k not in ("Male", "Female"))
        gender_chart.append({
            "designation": d["designation"],
            "male": male,
            "female": female,
            "other": other,
        })

    return {
        "total_designations": len(designations),
        "total_people": total,
        "designations": designations,
        "chart_data": chart_data,
        "gender_chart": gender_chart,
    }


def get_verified_breakdown(db: Session) -> dict:
    today = date.today()
    yesterday = today - timedelta(days=1)

    total_active = db.query(func.count(Person.id)).filter(Person.is_active == True).scalar() or 0
    total_men = db.query(func.count(Person.id)).filter(Person.is_active == True, Person.category == "Men").scalar() or 0
    total_women = db.query(func.count(Person.id)).filter(Person.is_active == True, Person.category == "Women").scalar() or 0
    total_stakeholders = db.query(func.count(Person.id)).filter(Person.is_active == True, Person.category == "Stakeholders").scalar() or 0

    alltime_total = db.query(func.count(Attendance.id)).filter(Attendance.status == "Verified").scalar() or 0
    alltime_gender = {r[0] or "Unspecified": r[1] for r in db.query(
        Attendance.gender, func.count(Attendance.id)
    ).filter(Attendance.status == "Verified").group_by(Attendance.gender).all()}
    alltime_cat = {r[0] or "Uncategorized": r[1] for r in db.query(
        Attendance.category, func.count(Attendance.id)
    ).filter(Attendance.status == "Verified").group_by(Attendance.category).all()}

    today_total = db.query(func.count(Attendance.id)).filter(
        cast(Attendance.verification_date, Date) == today, Attendance.status == "Verified"
    ).scalar() or 0
    today_gender = {r[0] or "Unspecified": r[1] for r in db.query(
        Attendance.gender, func.count(Attendance.id)
    ).filter(cast(Attendance.verification_date, Date) == today, Attendance.status == "Verified").group_by(Attendance.gender).all()}
    today_cat = {r[0] or "Uncategorized": r[1] for r in db.query(
        Attendance.category, func.count(Attendance.id)
    ).filter(cast(Attendance.verification_date, Date) == today, Attendance.status == "Verified").group_by(Attendance.category).all()}

    yesterday_total = db.query(func.count(Attendance.id)).filter(
        cast(Attendance.verification_date, Date) == yesterday, Attendance.status == "Verified"
    ).scalar() or 0
    yesterday_gender = {r[0] or "Unspecified": r[1] for r in db.query(
        Attendance.gender, func.count(Attendance.id)
    ).filter(cast(Attendance.verification_date, Date) == yesterday, Attendance.status == "Verified").group_by(Attendance.gender).all()}
    yesterday_cat = {r[0] or "Uncategorized": r[1] for r in db.query(
        Attendance.category, func.count(Attendance.id)
    ).filter(cast(Attendance.verification_date, Date) == yesterday, Attendance.status == "Verified").group_by(Attendance.category).all()}

    today_men = today_cat.get("Men", 0)
    today_women = today_cat.get("Women", 0)
    yesterday_men = yesterday_cat.get("Men", 0)
    yesterday_women = yesterday_cat.get("Women", 0)
    alltime_men = alltime_cat.get("Men", 0)
    alltime_women = alltime_cat.get("Women", 0)

    today_rate = round(today_total / total_active * 100, 1) if total_active > 0 else 0
    yesterday_rate = round(yesterday_total / total_active * 100, 1) if total_active > 0 else 0
    alltime_rate = round(alltime_total / total_active * 100, 1) if total_active > 0 else 0
    today_men_rate = round(today_men / total_men * 100, 1) if total_men > 0 else 0
    today_women_rate = round(today_women / total_women * 100, 1) if total_women > 0 else 0
    yesterday_men_rate = round(yesterday_men / total_men * 100, 1) if total_men > 0 else 0
    yesterday_women_rate = round(yesterday_women / total_women * 100, 1) if total_women > 0 else 0

    return {
        "total_active": total_active,
        "total_men": total_men,
        "total_women": total_women,
        "total_stakeholders": total_stakeholders,
        "yesterday": {
            "total": yesterday_total,
            "rate": yesterday_rate,
            "by_gender": yesterday_gender,
            "by_category": yesterday_cat,
            "men": yesterday_men,
            "women": yesterday_women,
            "men_rate": yesterday_men_rate,
            "women_rate": yesterday_women_rate,
        },
        "today": {
            "total": today_total,
            "rate": today_rate,
            "by_gender": today_gender,
            "by_category": today_cat,
            "men": today_men,
            "women": today_women,
            "men_rate": today_men_rate,
            "women_rate": today_women_rate,
        },
        "alltime": {
            "total": alltime_total,
            "rate": alltime_rate,
            "by_gender": alltime_gender,
            "by_category": alltime_cat,
            "men": alltime_men,
            "women": alltime_women,
        },
    }


def get_statistics_summary(db: Session) -> dict:
    today = date.today()
    weekly_start = today - timedelta(days=today.weekday())

    count_rows = db.query(
        Person.designation, Person.category, func.count(Person.id)
    ).filter(Person.is_active == True).group_by(Person.designation, Person.category).all()

    desig_totals = {}
    for desig, category, count in count_rows:
        key = _normalize_designation(desig, category)
        desig_totals[key] = desig_totals.get(key, 0) + count

    today_raw = db.query(
        Person.designation, Person.category, func.count(Attendance.id)
    ).join(Person, Attendance.person_id == Person.id).filter(
        cast(Attendance.verification_date, Date) == today,
        Attendance.status == "Verified",
    ).group_by(Person.designation, Person.category).all()
    today_map = {}
    for desig, category, count in today_raw:
        key = _normalize_designation(desig, category)
        today_map[key] = today_map.get(key, 0) + count

    week_raw = db.query(
        Person.designation, Person.category, func.count(Attendance.id)
    ).join(Person, Attendance.person_id == Person.id).filter(
        cast(Attendance.verification_date, Date) >= weekly_start,
        Attendance.status == "Verified",
    ).group_by(Person.designation, Person.category).all()
    week_map = {}
    for desig, category, count in week_raw:
        key = _normalize_designation(desig, category)
        week_map[key] = week_map.get(key, 0) + count

    rates = []
    for desig, total in desig_totals.items():
        if total > 0:
            rate = round(today_map.get(desig, 0) / total * 100, 1)
            rates.append(rate)

    rates_arr = np.array(rates) if rates else np.array([0.0])

    day_counts = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        c = db.query(func.count(Attendance.id)).filter(
            cast(Attendance.verification_date, Date) == d,
            Attendance.status == "Verified",
        ).scalar() or 0
        day_counts.append(c)
    day_arr = np.array(day_counts)

    return {
        "avg_attendance_rate": round(float(np.mean(rates_arr)), 1),
        "median_attendance_rate": round(float(np.median(rates_arr)), 1),
        "std_attendance_rate": round(float(np.std(rates_arr)), 1),
        "min_attendance_rate": round(float(np.min(rates_arr)), 1),
        "max_attendance_rate": round(float(np.max(rates_arr)), 1),
        "designations_above_80": int(np.sum(rates_arr >= 80)),
        "designations_below_50": int(np.sum(rates_arr < 50)),
        "total_designations": len(desig_totals),
        "daily_average": round(float(np.mean(day_arr)), 1),
        "daily_std": round(float(np.std(day_arr)), 1),
        "peak_day_count": int(np.max(day_arr)),
        "total_verified_week": int(np.sum(day_arr)),
    }
