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
    department = Column(String(64), default="", nullable=True)  # Bộ phận
    created_at = Column(DateTime, default=get_local_time)

    # === FIX: THÊM LẠI RELATIONSHIP ===
    guests = relationship("Guest", back_populates="registered_by", foreign_keys="[Guest.registered_by_user_id]")

class Guest(Base):
    __tablename__ = "guests"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), index=True, nullable=False)
    id_card_number = Column(String(32), index=True, default="")
    company = Column(String(128), index=True, default="")
    reason = Column(Text, default="")
    license_plate = Column(String(32), index=True, default="")
    supplier_name = Column(String(128), index=True, default="")
    status = Column(String(16), index=True, default="pending")
    
    estimated_datetime = Column(DateTime, nullable=True)
    
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_local_time)

    registered_by = relationship("User", back_populates="guests", foreign_keys=[registered_by_user_id])
    images = relationship("GuestImage", back_populates="guest", cascade="all, delete-orphan")

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

class LongTermGuest(Base):
    __tablename__ = "long_term_guests"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(128), nullable=False)
    id_card_number = Column(String(32), default="")
    company = Column(String(128), default="")
    reason = Column(Text, default="")
    license_plate = Column(String(32), default="")
    supplier_name = Column(String(128), default="")
    
    estimated_datetime = Column(DateTime, nullable=True)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=get_local_time)

    registered_by = relationship("User", foreign_keys=[registered_by_user_id])

# === ASSET MANAGEMENT MODELS ===

# Hằng số trạng thái
ASSET_STATUS_PENDING_OUT = "pending_out"
ASSET_STATUS_CHECKED_OUT = "checked_out"
ASSET_STATUS_RETURNED = "returned"

class AssetLog(Base):
    __tablename__ = "asset_log"
    id = Column(Integer, primary_key=True, index=True)
    
    # Thông tin người đăng ký
    registered_by_user_id = Column(Integer, ForeignKey("users.id"))
    registered_by = relationship("User", foreign_keys=[registered_by_user_id])
    full_name = Column(String(128), nullable=False)
    employee_code = Column(String(128), nullable=False)  # <--- Added to match DB
    department = Column(String(128), default="")
    
    # Thông tin đăng ký
    destination = Column(String(255), index=True, default="")
    description_reason = Column(Text, default="")
    asset_description = Column(Text, nullable=False)  # <--- Added to match DB
    quantity = Column(Integer, nullable=False, default=1)
    expected_return_date = Column(Date, nullable=True)
    
    # Trạng thái và Dấu vết
    status = Column(String(16), index=True, default=ASSET_STATUS_PENDING_OUT)
    
    # Dấu vết xác nhận RA
    check_out_time = Column(DateTime, nullable=True)
    check_out_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    check_out_by = relationship("User", foreign_keys=[check_out_by_user_id])
    
    # Dấu vết xác nhận VỀ
    check_in_back_time = Column(DateTime, nullable=True)
    check_in_back_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    check_in_back_by = relationship("User", foreign_keys=[check_in_back_by_user_id])

    created_at = Column(DateTime, default=get_local_time)
    
    # Image relationship
    images = relationship("AssetImage", back_populates="asset", cascade="all, delete-orphan")

class AssetImage(Base):
    __tablename__ = "asset_images"
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("asset_log.id"), nullable=False)
    image_path = Column(String(255), nullable=False)
    
    asset = relationship("AssetLog", back_populates="images")