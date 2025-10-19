import os, json
from dotenv import load_dotenv

load_dotenv()

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "./credentials.json")
LIVE_SHEET_ID = os.getenv("LIVE_SHEET_ID", "")
ARCHIVE_SHEETS = json.loads(os.getenv("ARCHIVE_SHEETS", "{}"))  # {'2024':'ID','2025':'ID'}
SHEET_NAME = os.getenv("SHEET_NAME", "Trang tính1")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Ho_Chi_Minh")
ALLOW_ORIGINS = [o.strip() for o in os.getenv("ALLOW_ORIGINS", "*").split(",")]
