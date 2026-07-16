import os
import uuid
from datetime import datetime, date
from typing import Optional
from fastapi import UploadFile


ALLOWED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def allowed_file(filename: str) -> bool:
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def save_upload_file(upload_file: UploadFile, upload_dir: str) -> Optional[str]:
    if not allowed_file(upload_file.filename or ""):
        return None
    os.makedirs(upload_dir, exist_ok=True)
    ext = os.path.splitext(upload_file.filename or "upload.xlsx")[1]
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_name)
    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())
    return file_path


def format_datetime(dt: Optional[datetime]) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%b %d, %Y %I:%M %p")


def format_date(dt: Optional[datetime]) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%b %d, %Y")


def get_client_ip(request) -> str:
    if request.client:
        return request.client.host
    return "unknown"
