from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey("persons.id"), nullable=False, index=True)
    person_name = Column(String(255), nullable=False)
    gender = Column(String(20), nullable=True)
    designation = Column(String(255), nullable=True)
    region_division = Column(String(255), nullable=True)
    category = Column(String(50), nullable=True)
    verification_time = Column(DateTime, default=datetime.utcnow)
    verification_date = Column(DateTime, default=datetime.utcnow)
    verified_by = Column(Integer, nullable=False)
    verified_by_name = Column(String(255), nullable=True)
    status = Column(String(50), default="Verified")
    remarks = Column(Text, nullable=True)
    is_overridden = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
