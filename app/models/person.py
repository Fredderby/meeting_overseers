from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from app.database import Base


class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    gender = Column(String(20), nullable=True, index=True)
    designation = Column(String(255), nullable=True, index=True)
    phone_number = Column(String(50), nullable=True, index=True)
    region_division = Column(String(255), nullable=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    remarks = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
