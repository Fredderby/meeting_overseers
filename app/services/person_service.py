from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.person import Person


def get_person(db: Session, person_id: int) -> Optional[Person]:
    return db.query(Person).filter(Person.id == person_id, Person.is_active == True).first()


def get_persons(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> Tuple[List[Person], int]:
    query = db.query(Person).filter(Person.is_active == True)
    if category:
        query = query.filter(Person.category == category)
    if search:
        q = f"%{search}%"
        query = query.filter(
            or_(
                Person.name.ilike(q),
                Person.designation.ilike(q),
                Person.phone_number.ilike(q),
                Person.region_division.ilike(q),
                Person.gender.ilike(q),
                Person.category.ilike(q),
                Person.remarks.ilike(q),
            )
        )
    total = query.count()
    persons = query.order_by(Person.name).offset(skip).limit(limit).all()
    return persons, total


def create_person(db: Session, **kwargs) -> Person:
    person = Person(**kwargs)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person


def update_person(db: Session, person_id: int, **kwargs) -> Optional[Person]:
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        return None
    for key, value in kwargs.items():
        if hasattr(person, key):
            setattr(person, key, value)
    db.commit()
    db.refresh(person)
    return person


def delete_person(db: Session, person_id: int) -> bool:
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        return False
    person.is_active = False
    db.commit()
    return True


def hard_delete_person(db: Session, person_id: int) -> bool:
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        return False
    db.delete(person)
    db.commit()
    return True


def get_all_persons(db: Session, category: Optional[str] = None) -> List[Person]:
    query = db.query(Person).filter(Person.is_active == True)
    if category:
        query = query.filter(Person.category == category)
    return query.order_by(Person.name).all()


def count_persons_by_category(db: Session) -> dict:
    from sqlalchemy import func
    rows = db.query(Person.category, func.count(Person.id)).filter(Person.is_active == True).group_by(Person.category).all()
    return {r[0] or "Uncategorized": r[1] for r in rows}


def count_persons_by_gender(db: Session) -> dict:
    from sqlalchemy import func
    rows = db.query(Person.gender, func.count(Person.id)).filter(Person.is_active == True).group_by(Person.gender).all()
    return {r[0] or "Unspecified": r[1] for r in rows}
