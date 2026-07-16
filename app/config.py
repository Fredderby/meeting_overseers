import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    APP_NAME: str = "Attendance Verification System"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "overseers")

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?connect_timeout=10"

    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin")
    ADMIN_SECRET: str = os.getenv("ADMIN_SECRET", "super-secret-key-change-in-prod")

    SECRET_KEY: str = os.getenv("SECRET_KEY", ADMIN_SECRET)
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    UPLOAD_FOLDER: str = os.getenv("UPLOAD_FOLDER", "uploads")
    EXPORT_FOLDER: str = os.getenv("EXPORT_FOLDER", "exports")

    SESSION_EXPIRE_MINUTES: int = 120
    MAX_UPLOAD_SIZE_MB: int = 10


settings = Settings()
