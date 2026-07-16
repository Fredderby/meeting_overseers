import os
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import pandas as pd

from app.models.person import Person


def detect_category(gender: Optional[str], designation: Optional[str] = None) -> str:
    if gender:
        g = gender.strip().lower()
        if g in ("male", "man", "men"):
            return "Men"
        if g in ("female", "woman", "women"):
            return "Women"
    if designation:
        d = designation.strip().lower()
        if "stakeholder" in d:
            return "Stakeholders"
    return "Stakeholders"


def parse_upload_file(filepath: str) -> List[Dict[str, Any]]:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath, dtype=str, keep_default_na=False)
    elif ext in (".xls", ".xlsx"):
        df = pd.read_excel(filepath, engine="openpyxl" if ext == ".xlsx" else "xlrd", dtype=str)
        df = df.fillna("")
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    df.columns = [c.strip() for c in df.columns]
    col_map = {}
    for c in df.columns:
        cl = c.lower().strip()
        if cl in ("name", "full name", "fullname", "names", "member name", "person name"):
            col_map["name"] = c
        elif cl in ("gender", "sex"):
            col_map["gender"] = c
        elif cl in ("designation", "title", "position", "role"):
            col_map["designation"] = c
        elif cl in ("phone", "phone number", "phone_number", "telephone", "tel", "mobile", "contact"):
            col_map["phone_number"] = c
        elif cl in ("region", "division", "region/division", "region_division", "area", "district", "location", "region/div", "reg_division"):
            col_map["region_division"] = c
        elif cl in ("remarks", "comment", "notes", "note", "remark"):
            col_map["remarks"] = c
        elif cl in ("category", "type", "group", "classification"):
            col_map["category"] = c

    if "name" not in col_map:
        raise ValueError("Could not find a 'Name' column in the file")

    records = []
    for _, row in df.iterrows():
        record = {}
        for target_key, source_col in col_map.items():
            raw = row[source_col]
            val = None
            if raw and raw.strip().lower() not in ("nan", "nat", "none", "na", "null", ""):
                val = raw.strip()
            record[target_key] = val
        if not record.get("name"):
            continue
        if not record.get("category"):
            record["category"] = detect_category(record.get("gender"), record.get("designation"))
        records.append(record)
    return records


def import_records(db: Session, records: List[Dict[str, Any]]) -> Dict[str, int]:
    imported = 0
    skipped = 0
    for rec in records:
        name = rec.get("name", "").strip()
        if not name:
            skipped += 1
            continue
        existing = db.query(Person).filter(Person.name.ilike(name), Person.is_active == True).first()
        if existing:
            for key in ("gender", "designation", "phone_number", "region_division", "category", "remarks"):
                if rec.get(key):
                    setattr(existing, key, rec[key])
            imported += 1
            continue
        person = Person(
            name=name,
            gender=rec.get("gender"),
            designation=rec.get("designation"),
            phone_number=rec.get("phone_number"),
            region_division=rec.get("region_division"),
            category=rec.get("category"),
            remarks=rec.get("remarks"),
        )
        db.add(person)
        imported += 1
    db.commit()
    return {"imported": imported, "skipped": skipped}
