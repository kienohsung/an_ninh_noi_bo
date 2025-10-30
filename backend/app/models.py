# File: security_mgmt_dev/backend/app/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, UniqueConstraint, Date
from sqlalchemy.orm import relationship
from datetime import datetime
import pytz
import os

from .database import Base
from .config import settings

def get_local_time():
    """Returns the current time in the timezone specified in settings."""
    tz = pytz.timezone(settings.TZ)
    return datetime.now(tz)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(String(16), nullable=False, index=True)  # admin, manager, guard, staff
    created_at = Column(DateTime, default=get_local_time)

    guests = relationship("Guest", back_populates="registered_by", foreign_keys="[Guest.registered_by_user_id]")

class Guest(Base):
    __tablename__ = "guests"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), index=True, nullable=False)
    id_card_number = Column(String(32), index=True, default="") # CCCD
    company = Column(String(128), index=True, default="")
    reason = Column(Text, default="")
    license_plate = Column(String(32), index=True, default="")
    supplier_name = Column(String(128), index=True, default="")
    status = Column(String(16), index=True, default="pending")  # pending, checked_in, checked_out
    
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa cột estimated_time cũ)
    # Thêm cột để lưu ngày VÀ giờ dự kiến khách vào
    estimated_datetime = Column(DateTime, nullable=True)
    # --- KẾT THÚC NÂNG CẤP ---
    
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_local_time)

    registered_by = relationship("User", back_populates="guests", foreign_keys=[registered_by_user_id])
    
    # Mối quan hệ mới: Một khách có nhiều ảnh
    images = relationship("GuestImage", back_populates="guest", cascade="all, delete-orphan")

# Bảng mới để lưu trữ ảnh của khách
class GuestImage(Base):
    __tablename__ = "guest_images"
    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    
    guest = relationship("Guest", back_populates="images")


class Supplier(Base):
    __tablename__ = "suppliers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(128), unique=True, index=True, nullable=False)

    plates = relationship("SupplierPlate", back_populates="supplier", cascade="all, delete-orphan")

class SupplierPlate(Base):
    __tablename__ = "supplier_plates"
    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    plate = Column(String(32), index=True, nullable=False)

    supplier = relationship("Supplier", back_populates="plates", foreign_keys=[supplier_id])
    __table_args__ = (UniqueConstraint("supplier_id", "plate", name="uq_supplier_plate"),)

# Bảng mới cho khách đăng ký dài hạn
class LongTermGuest(Base):
    __tablename__ = "long_term_guests"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), nullable=False)
    id_card_number = Column(String(32), default="")
    company = Column(String(128), default="")
    reason = Column(Text, default="")
    license_plate = Column(String(32), default="")
    supplier_name = Column(String(128), default="")
    
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa cột estimated_time cũ)
    # Thêm cột để lưu ngày VÀ giờ dự kiến khách vào
    estimated_datetime = Column(DateTime, nullable=True)
    # --- KẾT THÚC NÂNG CẤP ---
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_local_time)

    registered_by = relationship("User", foreign_keys=[registered_by_user_id])

