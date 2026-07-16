from app.database import get_db
from app.services.dashboard_service import get_dashboard_stats, get_designation_analytics, get_gender_distribution, get_category_distribution, get_weekly_trend
from datetime import date, timedelta
from sqlalchemy import func, cast, Date
from app.models.person import Person
from app.models.attendance import Attendance

db = next(get_db())

print("=== DASHBOARD STATS ===")
stats = get_dashboard_stats(db)
for k, v in stats.items():
    print(f"  {k}: {v}")

print("\n=== DESIGNATION ANALYTICS ===")
desig = get_designation_analytics(db)
print(f"  total_designations: {desig['total_designations']}")
print(f"  total_people: {desig['total_people']}")
total_verified = sum(d['verified_today'] for d in desig['designations'])
total_week = sum(d['verified_week'] for d in desig['designations'])
print(f"  sum of verified_today across designations: {total_verified}")
print(f"  sum of verified_week across designations: {total_week}")
print(f"  designations count: {len(desig['designations'])}")

print("\n=== RAW ATTENDANCE COUNTS ===")
today = date.today()
weekly_start = today - timedelta(days=today.weekday())
raw_today = db.query(func.count(Attendance.id)).filter(
    cast(Attendance.verification_date, Date) == today,
    Attendance.status == "Verified",
).scalar()
raw_week = db.query(func.count(Attendance.id)).filter(
    cast(Attendance.verification_date, Date) >= weekly_start,
    Attendance.status == "Verified",
).scalar()
raw_total_people = db.query(func.count(Person.id)).filter(Person.is_active == True).scalar()
print(f"  Raw today verified: {raw_today}")
print(f"  Raw week verified: {raw_week}")
print(f"  Raw total active people: {raw_total_people}")

print("\n=== GENDER DISTRIBUTION ===")
for g in get_gender_distribution(db):
    print(f"  {g}")

print("\n=== CATEGORY DISTRIBUTION ===")
for c in get_category_distribution(db):
    print(f"  {c}")

print("\n=== WEEKLY TREND ===")
for w in get_weekly_trend(db):
    print(f"  {w}")

db.close()
