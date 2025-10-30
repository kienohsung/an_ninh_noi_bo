# File: backend/app/schemas.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime, date

# ---------- AUTH ----------
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserBase(BaseModel):
    username: str
    full_name: str
    role: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    password: Optional[str] = None

class UserRead(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ---------- GUESTS & IMAGES ----------
class GuestImageRead(BaseModel):
    id: int
    image_path: str
    model_config = ConfigDict(from_attributes=True)

class GuestBase(BaseModel):
    full_name: str
    id_card_number: Optional[str] = ""
    company: Optional[str] = ""
    reason: Optional[str] = ""
    license_plate: Optional[str] = ""
    supplier_name: Optional[str] = ""
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class GuestCreate(GuestBase):
    pass

class GuestUpdate(BaseModel):
    full_name: Optional[str] = None
    id_card_number: Optional[str] = None
    company: Optional[str] = None
    reason: Optional[str] = None
    license_plate: Optional[str] = None
    supplier_name: Optional[str] = None
    status: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class GuestRead(GuestBase):
    id: int
    status: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    registered_by_user_id: Optional[int] = None
    created_at: datetime
    # estimated_datetime được kế thừa từ GuestBase
    model_config = ConfigDict(from_attributes=True)

class GuestReadWithUser(GuestRead):
    registered_by_name: Optional[str] = None
    images: List[GuestImageRead] = []

class GuestSuggestions(BaseModel):
    companies: List[str]
    license_plates: List[str]
    supplier_names: List[str]

class GuestIndividualCreate(BaseModel):
    full_name: str
    id_card_number: Optional[str] = ""

class GuestBulkCreate(BaseModel):
    guests: List[GuestIndividualCreate]
    company: Optional[str] = ""
    reason: Optional[str] = ""
    license_plate: Optional[str] = ""
    supplier_name: Optional[str] = ""
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class TokenRefreshRequest(BaseModel):
    refresh_token: str

# ---------- SUPPLIERS ----------
class SupplierBase(BaseModel):
    name: str

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None

class SupplierPlateBase(BaseModel):
    plate: str

class SupplierPlateCreate(SupplierPlateBase):
    pass

class SupplierPlateRead(SupplierPlateBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class SupplierRead(SupplierBase):
    id: int
    plates: List[SupplierPlateRead] = []
    model_config = ConfigDict(from_attributes=True)

# ---------- LONG TERM GUESTS ----------
class LongTermGuestBase(BaseModel):
    full_name: str
    id_card_number: Optional[str] = ""
    company: Optional[str] = ""
    reason: Optional[str] = ""
    license_plate: Optional[str] = ""
    supplier_name: Optional[str] = ""
    start_date: date
    end_date: date
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class LongTermGuestCreate(LongTermGuestBase):
    pass

class LongTermGuestUpdate(BaseModel):
    full_name: Optional[str] = None
    id_card_number: Optional[str] = None
    company: Optional[str] = None
    reason: Optional[str] = None
    license_plate: Optional[str] = None
    supplier_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    # --- NÂNG CẤP: Thay estimated_time bằng estimated_datetime ---
    # (Đã xóa trường estimated_time cũ)
    estimated_datetime: Optional[datetime] = None
    # --- KẾT THÚC NÂNG CẤP ---

class LongTermGuestRead(LongTermGuestBase):
    id: int
    is_active: bool
    registered_by_user_id: int
    created_at: datetime
    # estimated_datetime được kế thừa từ LongTermGuestBase
    model_config = ConfigDict(from_attributes=True)

# SỬA LỖI: Thêm schema LongTermGuestReadWithUser
class LongTermGuestReadWithUser(LongTermGuestRead):
    registered_by_name: Optional[str] = None

