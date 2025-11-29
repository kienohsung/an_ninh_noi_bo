# File: backend/app/main.py
import os
import logging
from datetime import datetime, date, time
import pytz

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from sqlalchemy import select
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .routers.admin_telegram import router as admin_telegram_router

# Nạp .env SỚM
try:
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=(Path(__file__).resolve().parent.parent / ".env"))
except Exception:
    pass

from .config import settings
from .database import Base, engine, SessionLocal
from .utils.logging_config import setup_logging
from . import models

# Routers
from .auth import router as auth_router, get_password_hash
from .routers.users import router as users_router
from .routers.guests import router as guests_router
from .routers.suppliers import router as suppliers_router
from .routers.reports import router as reports_router
from .routers.gemini import router as gemini_router
from .routers.long_term_guests import router as long_term_guests_router
from .routers.vehicle_log import router as vehicle_log_router
from .routers.guests_confirm import router as guests_confirm_router
from .routers.assets import router as assets_router

app = FastAPI(
    title="Ứng dụng an ninh nội bộ - Local Security App",
    version="2.7.0"
)

# Cài đặt logging
setup_logging()
logging.info("Application startup...")

# CORS Middleware
# CORS Middleware - EMERGENCY FIX
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # CHO PHÉP TẤT CẢ (chỉ để test)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Tạo CSDL (nếu chưa có) và thư mục
try:
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception as e:
    logging.error(f"Error initializing database or directories: {e}")

# Include Routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(guests_router)
app.include_router(suppliers_router)
app.include_router(reports_router)
app.include_router(gemini_router)
app.include_router(long_term_guests_router)
app.include_router(vehicle_log_router)
app.include_router(guests_confirm_router)
app.include_router(admin_telegram_router)
app.include_router(assets_router)

# Mount static files
app.mount(f"/{os.path.basename(settings.UPLOAD_DIR)}", StaticFiles(directory=settings.UPLOAD_DIR), name="static")

# Khởi tạo admin user
@app.on_event("startup")
def on_startup():
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == settings.ADMIN_USERNAME).first()
        if not admin_user:
            admin_password_hash = get_password_hash(settings.ADMIN_PASSWORD)
            db_admin = models.User(
                username=settings.ADMIN_USERNAME,
                password_hash=admin_password_hash,
                full_name="Administrator",  # Sửa: thêm full_name
                role="admin"
            )
            db.add(db_admin)
            db.commit()
            logging.info(f"Admin user '{settings.ADMIN_USERNAME}' created.")
    except Exception as e:
        logging.error(f"Error creating admin user: {e}")
    finally:
        db.close()

    # Job cho Khách dài hạn
    def create_daily_guest_entries():
        """Hàm chạy nền để tạo khách vãng lai từ danh sách dài hạn."""
        logging.info("[long_term] Job started: Creating daily guest entries...")
        db = SessionLocal()
        try:
            today = datetime.now(pytz.timezone(settings.TZ)).date()
            
            active_long_term_guests = db.scalars(
                select(models.LongTermGuest).where(
                    models.LongTermGuest.is_active == True,
                    models.LongTermGuest.start_date <= today,
                    models.LongTermGuest.end_date >= today
                )
            ).all()

            system_user = db.scalars(select(models.User).where(models.User.username == 'system')).first()
            if not system_user:
                logging.warning("[long_term] 'system' user not found. Skipping job.")
                return

            start_of_day = datetime.combine(today, time.min, tzinfo=pytz.timezone(settings.TZ))
            end_of_day = datetime.combine(today, time.max, tzinfo=pytz.timezone(settings.TZ))

            existing_guests_today = db.scalars(
                select(models.Guest.id_card_number).where(
                    models.Guest.registered_by_user_id == system_user.id,
                    models.Guest.created_at >= start_of_day,
                    models.Guest.created_at <= end_of_day,
                    models.Guest.id_card_number != ""
                )
            ).all()
            existing_guest_set = set(existing_guests_today)

            count = 0
            for lt_guest in active_long_term_guests:
                if lt_guest.id_card_number and lt_guest.id_card_number not in existing_guest_set:
                    new_guest = models.Guest(
                        full_name=lt_guest.full_name,
                        id_card_number=lt_guest.id_card_number,
                        company=lt_guest.company or lt_guest.supplier_name,
                        reason=lt_guest.reason or "Khách đăng ký dài hạn",
                        license_plate=lt_guest.license_plate,
                        supplier_name=lt_guest.supplier_name,
                        estimated_datetime=lt_guest.estimated_datetime,
                        status="pending",
                        registered_by_user_id=system_user.id,
                        created_at=models.get_local_time()
                    )
                    db.add(new_guest)
                    existing_guest_set.add(lt_guest.id_card_number)
                    count += 1
            
            if count > 0:
                db.commit()
                logging.info(f"[long_term] Job finished: Created {count} new daily guest(s).")
            else:
                logging.info("[long_term] Job finished: No new guests needed to be created.")

        except Exception as e:
            logging.error(f"[long_term] Job failed: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

    # Chạy ngay khi startup
    try:
        create_daily_guest_entries()
        logging.info("[long_term] Startup run completed.")
    except Exception as e:
        logging.error(f"[long_term] Startup run failed: {e}", exc_info=True)

    # Bắt đầu scheduler
    try:
        sched = BackgroundScheduler(timezone=settings.TZ)
        sched.add_job(
            create_daily_guest_entries,
            trigger=IntervalTrigger(minutes=60),
            id="create_daily_guests_job",
            name="Create daily guest entries from long-term registrations",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
            misfire_grace_time=30,
        )
        sched.start()
        app.state.scheduler = sched
        logging.info(f"[long_term] Scheduler started: every 60 minutes (TZ={settings.TZ}).")
    except Exception as e:
        logging.error(f"[long_term] Could not start the scheduler: {e}", exc_info=True)


@app.on_event("shutdown")
def on_shutdown():
    try:
        sched = getattr(app.state, "scheduler", None)
        if sched:
            sched.shutdown()
            logging.info("[long_term] Scheduler shut down.")
    except Exception as e:
        logging.error(f"Error shutting down scheduler: {e}", exc_info=True)

@app.get("/")
def read_root():
    return {"message": "Welcome to Local Security API", "version": app.version}