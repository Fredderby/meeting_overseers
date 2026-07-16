import os
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.models import User, Person, Attendance, AuditLog
from app.authentication.auth import hash_password
from app.middleware.middleware import AppMiddleware
from app.routers import (
    auth, dash_router, people, attendance, upload_router,
    export_router, profile, audit, search, analytics, settings as settings_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(settings.EXPORT_FOLDER, exist_ok=True)
    try:
        Base.metadata.create_all(bind=engine)
        _create_admin_user()
    except Exception as e:
        print(f"WARNING: Database connection failed: {e}")
    try:
        yield
    except asyncio.CancelledError:
        pass


def _create_admin_user():
    from app.database import SessionLocal
    try:
        db = SessionLocal()
        try:
            existing = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
            if not existing:
                admin = User(
                    username=settings.ADMIN_USERNAME,
                    password_hash=hash_password(settings.ADMIN_PASSWORD),
                    role="Administrator",
                    full_name="System Administrator",
                    is_active=True,
                )
                db.add(admin)
                db.commit()
                print(f"Admin user '{settings.ADMIN_USERNAME}' created")
        finally:
            db.close()
    except Exception as e:
        print(f"WARNING: Could not create admin user: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

app.add_middleware(AppMiddleware, requests_per_minute=120)

app.include_router(auth.router)
app.include_router(dash_router.router)
app.include_router(people.router)
app.include_router(attendance.router)
app.include_router(upload_router.router)
app.include_router(export_router.router)
app.include_router(profile.router)
app.include_router(audit.router)
app.include_router(search.router)
app.include_router(analytics.router)
app.include_router(settings_router.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard")


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return RedirectResponse(url="/dashboard")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
    )
