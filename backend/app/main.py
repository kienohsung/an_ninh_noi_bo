# File: backend/app/main.py
import os
import logging
import pytz
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, time, datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .database import Base, engine, SessionLocal
from .utils.logging_config import setup_logging
from . import models

# (GIẢI PHÁP DỨT ĐIỂM) Import tường minh từng router object từ file cụ thể của nó
from .auth import router as auth_router, get_password_hash
from .routers.users import router as users_router
from .routers.guests import router as guests_router
from .routers.suppliers import router as suppliers_router
from .routers.reports import router as reports_router
from .routers.gemini import router as gemini_router
from .routers.long_term_guests import router as long_term_guests_router
from .routers.vehicle_log import router as vehicle_log_router

app = FastAPI(title="Ứng dụng an ninh nội bộ - Local Security App", version="2.6.2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static Files cho ảnh upload
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Khai báo tất cả các router
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(guests_router)
app.include_router(suppliers_router)
app.include_router(reports_router)
app.include_router(gemini_router)
app.include_router(long_term_guests_router)
app.include_router(vehicle_log_router)

# --- Tác vụ nền cho khách dài hạn (giữ nguyên) ---
def create_daily_guest_entries():
    db: Session = SessionLocal()
    try:
        today = date.today()
        logger = logging.getLogger(__name__)
        logger.info(f"Running scheduled job to create daily guest entries for {today}...")

        active_long_term_guests = db.query(models.LongTermGuest).filter(
            models.LongTermGuest.is_active == True,
            models.LongTermGuest.start_date <= today,
            models.LongTermGuest.end_date >= today
        ).all()

        count = 0
        for lt_guest in active_long_term_guests:
            already_exists = db.query(models.Guest).filter(
                models.Guest.full_name == lt_guest.full_name,
                models.Guest.id_card_number == lt_guest.id_card_number,
                func.date(models.Guest.created_at) == today
            ).first()

            if not already_exists:
                tz = pytz.timezone(settings.TZ)
                creation_time = tz.localize(datetime.combine(today, time(8, 0)))
                new_guest = models.Guest(
                    full_name=lt_guest.full_name,
                    id_card_number=lt_guest.id_card_number,
                    company=lt_guest.company,
                    reason=f"Khách dài hạn: {lt_guest.reason or ''}",
                    license_plate=lt_guest.license_plate,
                    supplier_name=lt_guest.supplier_name,
                    status="pending",
                    registered_by_user_id=lt_guest.registered_by_user_id,
                    created_at=creation_time
                )
                db.add(new_guest)
                count += 1
        
        if count > 0:
            db.commit()
        logger.info(f"Job finished. Created {count} new daily guest entries.")

    except Exception as e:
        logging.error(f"Failed to create daily guest entries: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

# --- Sự kiện khởi động ứng dụng (giữ nguyên) ---
@app.on_event("startup")
def on_startup():
    setup_logging()
    Base.metadata.create_all(bind=engine)
    
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "guests"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "archived_guests"), exist_ok=True)

    db: Session = SessionLocal()
    try:
        admin = db.query(models.User).filter_by(username=settings.ADMIN_USERNAME).first()
        if not admin:
            admin = models.User(
                username=settings.ADMIN_USERNAME,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                full_name="Administrator",
                role="admin"
            )
            db.add(admin); db.commit()
    finally:
        db.close()
        
    try:
        scheduler = BackgroundScheduler(timezone=settings.TZ)
        scheduler.add_job(
            create_daily_guest_entries,
            trigger=CronTrigger(hour=8, minute=0),
            id="create_daily_guests_job",
            name="Create daily guest entries from long-term registrations",
            replace_existing=True
        )
        scheduler.start()
        logging.info(f"Scheduler for long-term guests started. Will run daily at 08:00 (Timezone: {settings.TZ}).")
    except Exception as e:
        logging.error(f"Could not start the scheduler: {e}", exc_info=True)

