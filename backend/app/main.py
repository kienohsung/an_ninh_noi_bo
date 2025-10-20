# File: backend/app/main.py
import os
import logging
from datetime import datetime, date, time
import pytz

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# Nạp .env SỚM (main.py ở backend/app/, .env ở backend/.env)
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

app = FastAPI(
    title="Ứng dụng an ninh nội bộ - Local Security App",
    version="2.6.4"
)

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

# Khai báo tất cả router
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(guests_router)
app.include_router(suppliers_router)
app.include_router(reports_router)
app.include_router(gemini_router)
app.include_router(long_term_guests_router)
app.include_router(vehicle_log_router)


# =========================================================
# JOB: Tạo bản ghi khách hằng ngày cho khách dài hạn
# - Dùng khoảng thời gian trong ngày theo TZ để tránh lệch múi giờ
# - Có thể gọi trực tiếp (startup) và gọi theo lịch (scheduler)
# =========================================================
def create_daily_guest_entries():
    """
    Duyệt các LongTermGuest đang hiệu lực trong NGÀY (theo TZ),
    nếu trong ngày CHƯA có Guest tương ứng thì tạo bản ghi mới (status='pending').
    """
    db: Session = SessionLocal()
    try:
        tz = pytz.timezone(settings.TZ)
        now_tz = datetime.now(tz)
        start_of_day = tz.localize(datetime.combine(now_tz.date(), time.min))
        end_of_day   = tz.localize(datetime.combine(now_tz.date(), time.max))

        logger = logging.getLogger(__name__)
        logger.info(f"[long_term] Run job for {now_tz:%Y-%m-%d %H:%M:%S %Z}")

        active_long_term_guests = db.query(models.LongTermGuest).filter(
            models.LongTermGuest.is_active.is_(True),
            models.LongTermGuest.start_date <= now_tz.date(),
            models.LongTermGuest.end_date >= now_tz.date(),
        ).all()

        created_count = 0
        for lt in active_long_term_guests:
            # Đã có bản ghi trong ngày?
            exists = db.query(models.Guest).filter(
                models.Guest.full_name == lt.full_name,
                models.Guest.id_card_number == lt.id_card_number,
                models.Guest.created_at >= start_of_day,
                models.Guest.created_at <= end_of_day,
            ).first()

            if not exists:
                new_guest = models.Guest(
                    full_name=lt.full_name,
                    id_card_number=lt.id_card_number,
                    # NOTE: nếu schema Guest không có 'company', đổi sang field đúng (vd: organization) hoặc bỏ.
                    company=getattr(lt, "company", None),
                    reason=f"Khách dài hạn: {lt.reason or ''}",
                    license_plate=lt.license_plate,
                    supplier_name=lt.supplier_name,
                    status="pending",
                    registered_by_user_id=lt.registered_by_user_id,
                    created_at=now_tz,  # theo TZ
                )
                db.add(new_guest)
                created_count += 1

        if created_count:
            db.commit()
        logger.info(f"[long_term] Created {created_count} new daily guests.")
    except Exception as e:
        logging.error(f"[long_term] Job failed: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


# =========================================================
# STARTUP / SHUTDOWN
# - Khởi tạo DB, admin mặc định
# - Chạy NGAY job create_daily_guest_entries() ở thời điểm khởi động
# - Khởi động scheduler quét mỗi 1 phút và giữ tham chiếu trong app.state
# - Tắt scheduler gọn khi shutdown
# =========================================================
@app.on_event("startup")
def on_startup():
    setup_logging()
    Base.metadata.create_all(bind=engine)

    # Chuẩn bị thư mục upload
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "guests"), exist_ok=True)
    os.makedirs(os.path.join(settings.UPLOAD_DIR, "archived_guests"), exist_ok=True)

    # Tạo admin mặc định (nếu chưa có)
    db: Session = SessionLocal()
    try:
        admin = db.query(models.User).filter_by(username=settings.ADMIN_USERNAME).first()
        if not admin:
            admin = models.User(
                username=settings.ADMIN_USERNAME,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
                full_name="Administrator",
                role="admin",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

    # 1) CHẠY NGAY JOB khi server khởi động
    try:
        create_daily_guest_entries()
        logging.info("[long_term] Startup run completed.")
    except Exception as e:
        logging.error(f"[long_term] Startup run failed: {e}", exc_info=True)

    # 2) BẮT ĐẦU SCHEDULER: chạy mỗi 1 phút
    try:
        sched = BackgroundScheduler(timezone=settings.TZ)
        sched.add_job(
            create_daily_guest_entries,
            trigger=IntervalTrigger(minutes=60),
            id="create_daily_guests_job",
            name="Create daily guest entries from long-term registrations",
            replace_existing=True,
            coalesce=True,        # gom job nếu bị lỡ nhịp (sleep/restart)
            max_instances=1,
            misfire_grace_time=30,
        )
        sched.start()
        app.state.scheduler = sched  # giữ tham chiếu để tránh GC
        logging.info(f"[long_term] Scheduler started: every 1 minute (TZ={settings.TZ}).")
    except Exception as e:
        logging.error(f"[long_term] Could not start the scheduler: {e}", exc_info=True)


@app.on_event("shutdown")
def on_shutdown():
    try:
        sched = getattr(app.state, "scheduler", None)
        if sched:
            sched.shutdown(wait=False)
            logging.info("[long_term] Scheduler shutdown done.")
    except Exception as e:
        logging.warning(f"[long_term] Scheduler shutdown error: {e}")
