# File path: backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./security_v2_3.db"
    SECRET_KEY: str = "change_me_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480 # 8 hours
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080 # 7 days
    ALGORITHM: str = "HS256"
    # SỬA LỖI: Thêm địa chỉ IP mạng làm giá trị mặc định để tăng tính linh hoạt
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

    # --- THÊM MỚI: URL của service trích xuất CCCD ---
    ID_CARD_EXTRACTOR_URL: str = "http://127.0.0.1:5009/extract"


settings = Settings(_env_file=os.path.join(os.path.dirname(__file__), "..", ".env"), _env_file_encoding="utf-8")
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

