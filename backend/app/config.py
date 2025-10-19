# BACKEND/app/config.py
import os
import json
from dotenv import load_dotenv

# Nạp .env (nếu có lỗi format vẫn bỏ qua, để server không chết khi import)
try:
    load_dotenv()
except Exception:
    pass

def _safe_json_or_pairs(val: str) -> dict:
    """
    Parse ARCHIVE_SHEETS từ JSON hoặc dạng "2024=idA;2025=idB".
    """
    if not val:
        return {}
    # thử JSON
    try:
        obj = json.loads(val)
        if isinstance(obj, dict):
            return {str(k): str(v) for k, v in obj.items()}
    except Exception:
        pass
    # thử dạng cặp key=value;key=value
    out = {}
    for part in [p.strip() for p in val.split(";") if p.strip()]:
        if "=" in part:
            k, v = part.split("=", 1)
            out[k.strip()] = v.strip()
    return out

class Settings:
    # Các biến môi trường & mặc định an toàn
    GSHEETS_CREDENTIALS_PATH: str = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./credentials.json")
    GSHEETS_LIVE_SHEET_ID: str = os.getenv("LIVE_SHEET_ID", "").strip()
    GSHEETS_ARCHIVE_SHEETS: dict = _safe_json_or_pairs(os.getenv("ARCHIVE_SHEETS", ""))
    GSHEETS_SHEET_NAME: str = os.getenv("SHEET_NAME", "Trang tính1")
    TZ: str = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
    # Database (mặc định dùng SQLite file local)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")

    # CORS
    _raw_allow = os.getenv("ALLOW_ORIGINS", "*").strip()
    if _raw_allow == "*":
        ALLOW_ORIGINS = ["*"]
    else:
        ALLOW_ORIGINS = [o.strip() for o in _raw_allow.split(",") if o.strip()]

# Tạo instance settings cho các module khác import
settings = Settings()

__all__ = ["settings"]
