# File: backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os
import json

class Settings(BaseSettings):
    # Cấu hình gốc của dự án
    DATABASE_URL: str = "sqlite:///./security_v2_3.db"
    SECRET_KEY: str = "change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480 # 8 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 days
    ALGORITHM: str = "HS256"
    CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://192.168.223.176:5173",
        "http://192.168.223.176:5174"
    ]
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    TZ: str = "Asia/Bangkok"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    GEMINI_API_KEY: Optional[str] = None
    ID_CARD_EXTRACTOR_URL: str = "http://127.0.0.1:5009/extract"

    # --- Cấu hình mới cho Google Sheets ---
    GSHEETS_CREDENTIALS_PATH: str = "credentials.json"
    GSHEETS_LIVE_SHEET_ID: str = ""
    GSHEETS_ARCHIVE_MAP_JSON: str = "{}" # e.g., '{"2024": "id1", "2025": "id2"}'
    GSHEETS_SHEET_NAME: str = "Trang tính1"

    class Config:
        # Pydantic V2 config
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = "utf-8"

# Tạo một instance duy nhất của Settings
settings = Settings()

# Đảm bảo thư mục upload tồn tại
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

