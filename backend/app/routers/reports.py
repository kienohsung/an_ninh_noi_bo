# File: security_mgmt_dev/backend/app/routers/reports.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, time
import logging

from .. import models
from ..deps import get_db
from ..auth import require_roles

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(require_roles("admin", "manager"))])
logger = logging.getLogger(__name__)

def apply_time_filters(query, model, start: datetime | None, end: datetime | None):
    """
    Áp dụng bộ lọc thời gian cho một câu truy vấn SQLAlchemy.
    Sử dụng cột 'check_in_time' để lọc.
    """
    time_column = model.check_in_time
    if start:
        query = query.filter(time_column >= start)
    if end:
        # Frontend đã gửi mốc thời gian chính xác (23:59:59),
        # nên chỉ cần so sánh nhỏ hơn hoặc bằng.
        query = query.filter(time_column <= end)
    return query

@router.get("/guests_daily")
def guests_daily(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách vào theo từng ngày."""
    try:
        # Bỏ điều kiện lọc theo biển số, đếm tất cả khách đã check-in
        query = db.query(func.date(models.Guest.check_in_time), func.count(models.Guest.id))\
                  .filter(models.Guest.status == "checked_in")
        
        query = apply_time_filters(query, models.Guest, start, end)
        data = query.group_by(func.date(models.Guest.check_in_time)).order_by(func.date(models.Guest.check_in_time)).all()
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_daily: {e}", exc_info=True)
        return {"labels": [], "series": []}

@router.get("/guests_by_user")
def guests_by_user(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách theo người đăng ký."""
    try:
        # Bỏ điều kiện lọc theo biển số, đếm tất cả khách đã check-in
        query = db.query(models.User.full_name, func.count(models.Guest.id))\
                  .join(models.User, models.Guest.registered_by_user_id == models.User.id)\
                  .filter(models.Guest.status == "checked_in")

        query = apply_time_filters(query, models.Guest, start, end)
        data = query.group_by(models.User.full_name).all()
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_by_user: {e}", exc_info=True)
        return {"labels": [], "series": []}

@router.get("/guests_by_supplier")
def guests_by_supplier(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None):
    """Thống kê lượt khách theo nhà cung cấp."""
    try:
        # Bỏ điều kiện lọc theo biển số, đếm tất cả khách đã check-in
        query = db.query(models.Guest.supplier_name, func.count(models.Guest.id))\
                  .filter(models.Guest.status == "checked_in", models.Guest.supplier_name != "")
        
        query = apply_time_filters(query, models.Guest, start, end)
        data = query.group_by(models.Guest.supplier_name).all()
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_by_supplier: {e}", exc_info=True)
        return {"labels": [], "series": []}

@router.get("/guests_by_plate")
def guests_by_plate(db: Session = Depends(get_db), start: datetime | None = None, end: datetime | None = None, limit: int = 10):
    """Thống kê top 10 xe vào nhiều nhất (vẫn giữ nguyên logic yêu cầu biển số)."""
    try:
        query = db.query(models.Guest.license_plate, func.count(models.Guest.id))\
                  .filter(models.Guest.status == "checked_in", models.Guest.license_plate != "", models.Guest.license_plate != None)
        
        query = apply_time_filters(query, models.Guest, start, end)
        
        data = query.group_by(models.Guest.license_plate)\
                   .order_by(desc(func.count(models.Guest.id)))\
                   .limit(limit)\
                   .all()
        
        if not data:
            return {"labels": [], "series": []}
            
        return {"labels": [str(d or "") for d, _ in data], "series": [c for _, c in data]}
    except Exception as e:
        logger.error(f"Error in guests_by_plate: {e}", exc_info=True)
        return {"labels": [], "series": []}

