# BACKEND/app/database.py
from __future__ import annotations

import unicodedata
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


# -----------------------------
# 1) Tiện ích: bỏ dấu tiếng Việt (dùng cho SQLite)
# -----------------------------
def unaccent_string(text: str) -> str:
    """
    Loại bỏ dấu (accent) khỏi chuỗi.
    Hoạt động tốt với so khớp không phân biệt hoa/thường (dùng ILIKE/LOWER ở tầng truy vấn).
    """
    if not isinstance(text, str):
        return text
    try:
        nfkd_form = unicodedata.normalize("NFD", text)
        return "".join(c for c in nfkd_form if not unicodedata.combining(c))
    except Exception:
        return text


# -----------------------------
# 2) Engine & Session
# -----------------------------
DATABASE_URL = getattr(settings, "DATABASE_URL", "sqlite:///./app.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite cần tùy chọn này để làm việc tốt trong môi trường đa luồng
    connect_args = {"check_same_thread": False}

# Tùy bạn có thể thêm pool_pre_ping=True nếu dùng Postgres/MySQL để tránh connection stale
engine: Engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    future=True,
)

# Đăng ký các hook dành riêng cho SQLite
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_on_connect(dbapi_connection, connection_record):
        # Bật ràng buộc khóa ngoại
        try:
            dbapi_connection.execute("PRAGMA foreign_keys=ON;")
        except Exception:
            pass

        # Đăng ký hàm unaccent(text) cho SQLite
        try:
            dbapi_connection.create_function("unaccent", 1, unaccent_string)
        except Exception:
            # Nếu đã tạo rồi thì bỏ qua
            pass


# Factory tạo Session
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

# Base để các model thừa kế
Base = declarative_base()


# -----------------------------
# 3) Dependency cho FastAPI
# -----------------------------
def get_db() -> Generator:
    """
    Dependency chuẩn cho FastAPI.
    Ví dụ dùng:
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
