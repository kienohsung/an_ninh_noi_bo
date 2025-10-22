# File: backend/app/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional, Dict
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
        "http://127.0.0.1:5173", "http://localhost:5173",
        "http://127.0.0.1:5174", "http://localhost:5174",
        "http://192.168.223.176:5173", "http://192.168.223.176:5174"
    ]
    UPLOAD_DIR: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
    TZ: str = "Asia/Bangkok"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    GEMINI_API_KEY: Optional[str] = None
    ID_CARD_EXTRACTOR_URL: str = "http://127.0.0.1:5009/extract"

    # --- SỬA LỖI: Thêm các biến môi trường cho Telegram vào đây ---
    NOTIFY_TELEGRAM_ENABLED: bool = False
    TELEGRAM_BOT_TOKEN: str = "8014586502:AAFSMiARi8xIB6d26vaGiHbr-QQciJFDd5k"
    TELEGRAM_CHAT_ID: str = "-1003121251250"
    # ---------------------------------------------------------
    # --- CẢI TIẾN: Thêm ID chat lưu trữ (sử dụng Chat ID bạn cung cấp) ---
    TELEGRAM_ARCHIVE_CHAT_ID: Optional[str] = "-4884291349"

    # --- Cấu hình mới cho Google Sheets ---
    GSHEETS_CREDENTIALS_PATH: str = "credentials.json"
    GSHEETS_LIVE_SHEET_ID: str = "1zenHc1PuDHvVcuctJnTVp8tdD-3xWMf36ozynLk7jHw"
    
    # SỬA LỖI: Đổi tên biến GSHEETS_ARCHIVE_MAP_JSON thành GSHEETS_ARCHIVE_SHEETS
    # và thay đổi kiểu dữ liệu để nó tự động parse JSON
    GSHEETS_ARCHIVE_SHEETS: Dict[str, str] = {} # e.g., {"2024": "id1", "2025": "id2"}
    GSHEETS_SHEET_NAME: str = "Trang tính1"

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = "utf-8"

settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
