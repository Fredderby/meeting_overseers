from datetime import datetime, date
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date

from app.models.audit_log import AuditLog
from app.models.user import User


def create_log(
    db: Session,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: Optional[int] = None,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user_id: Optional[int] = None,
) -> Tuple[List[AuditLog], int]:
    query = db.query(AuditLog)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if date_from:
        query = query.filter(cast(AuditLog.timestamp, Date) >= date_from)
    if date_to:
        query = query.filter(cast(AuditLog.timestamp, Date) <= date_to)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    total = query.count()
    logs = query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    return logs, total


def get_logs_by_date_range(db: Session, start_date: date, end_date: date) -> List[AuditLog]:
    return db.query(AuditLog).filter(
        cast(AuditLog.timestamp, Date) >= start_date,
        cast(AuditLog.timestamp, Date) <= end_date,
    ).order_by(AuditLog.timestamp.desc()).all()
