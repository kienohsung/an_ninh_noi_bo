# File: security_mgmt_dev/backend/app/deps.py
from typing import Generator
from .database import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
