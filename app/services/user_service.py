from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.authentication.auth import hash_password


def get_users(db: Session, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> Tuple[List[User], int]:
    query = db.query(User)
    if search:
        like = f"%{search}%"
        query = query.filter(
            (User.username.ilike(like)) |
            (User.full_name.ilike(like)) |
            (User.email.ilike(like))
        )
    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return users, total


def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, username: str, password: str, full_name: str = "", email: str = "", role: str = "Verifier") -> User:
    user = User(
        username=username.strip(),
        password_hash=hash_password(password),
        full_name=full_name.strip() or None,
        email=email.strip() or None,
        role=role.strip(),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, full_name: str = None, email: str = None, role: str = None, is_active: bool = None) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    if full_name is not None:
        user.full_name = full_name.strip() or None
    if email is not None:
        user.email = email.strip() or None
    if role is not None:
        user.role = role.strip()
    if is_active is not None:
        user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def reset_password(db: Session, user_id: int, new_password: str) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


def get_user_stats(db: Session) -> dict:
    total = db.query(func.count(User.id)).scalar()
    active = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    admins = db.query(func.count(User.id)).filter(User.role == "Administrator").scalar()
    verifiers = db.query(func.count(User.id)).filter(User.role == "Verifier").scalar()
    return {"total": total, "active": active, "admins": admins, "verifiers": verifiers}
