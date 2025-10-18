# File: security_mgmt_dev/backend/app/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base
import unicodedata
from .config import settings

def unaccent_string(text: str) -> str:
    """Removes accents from a string. Case is handled by ilike."""
    if not isinstance(text, str):
        return text
    try:
        # Normalize to NFD form to separate base characters from combining characters
        nfkd_form = unicodedata.normalize('NFD', text)
        # Keep only non-combining characters (i.e., remove accents)
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except Exception:
        return text

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {})

# For SQLite, we need to register a custom UNACCENT function for every connection
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def connect(dbapi_connection, connection_record):
        dbapi_connection.create_function("unaccent", 1, unaccent_string)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
