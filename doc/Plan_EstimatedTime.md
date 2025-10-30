Tuyệt vời. Tôi đã tiếp nhận các yêu cầu chi tiết của bạn. Việc bổ sung trường **"Giờ dự kiến"** (`estimated_time`) và các logic cảnh báo liên quan là một cải tiến toàn diện, bao gồm cập nhật cả Backend (Database, API, Telegram Noti) và Frontend (UI, Logic cảnh báo).

Dưới đây là các thay đổi mã nguồn chi tiết để triển khai tính năng này:

-----

## 1\. Thay đổi ở Backend (Database, Schema, API & Logic)

Tôi sẽ cập nhật 6 file Backend cốt lõi để đảm bảo tính năng hoạt động xuyên suốt từ dữ liệu thô đến logic nghiệp vụ và thông báo.

### 1.1. Thêm cột `estimated_time` vào Models (`backend/app/models.py`)

Thêm cột `estimated_time` kiểu `String(16)` vào cả hai bảng `Guest` và `LongTermGuest`.

```python
# File: backend/app/models.py

# ... (các imports khác)
from .database import Base
from .config import settings

def get_local_time():
# ... (hàm giữ nguyên)

class User(Base):
# ... (model giữ nguyên)

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
    # --- THÊM MỚI: Giờ dự kiến khách vào (HH:MM) ---
    estimated_time = Column(String(16), default="")
    # --- KẾT THÚC THÊM MỚI ---
    check_in_time = Column(DateTime, nullable=True)
    # ... (các cột khác giữ nguyên)

# ... (các models khác giữ nguyên)

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
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    # --- THÊM MỚI: Giờ dự kiến khách vào (HH:MM) ---
    estimated_time = Column(String(16), default="")
    # --- KẾT THÚC THÊM MỚI ---
    is_active = Column(Boolean, default=True)
    # ... (các cột khác giữ nguyên)
```

### 1.2. Cập nhật Schema (`backend/app/schemas.py`)

Bổ sung `estimated_time` vào các schema liên quan để API có thể nhận và trả về dữ liệu này.

```python
# File: backend/app/schemas.py

# ... (các imports khác)

class GuestBase(BaseModel):
    full_name: str
    id_card_number: Optional[str] = ""
    company: Optional[str] = ""
    reason: Optional[str] = ""
    license_plate: Optional[str] = ""
    supplier_name: Optional[str] = ""
    # --- THÊM MỚI: Giờ dự kiến ---
    estimated_time: Optional[str] = ""
    # --- KẾT THÚC THÊM MỚI ---

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
    # --- THÊM MỚI: Giờ dự kiến ---
    estimated_time: Optional[str] = None
    # --- KẾT THÚC THÊM MỚI ---

class GuestRead(GuestBase):
    id: int
    status: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    registered_by_user_id: Optional[int] = None
    created_at: datetime
    # estimated_time đã được kế thừa từ GuestBase
    model_config = ConfigDict(from_attributes=True)

# ... (các schemas khác giữ nguyên)

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
    # --- THÊM MỚI: Giờ dự kiến ---
    estimated_time: Optional[str] = ""
    # --- KẾT THÚC THÊM MỚI ---

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
    # --- THÊM MỚI: Giờ dự kiến ---
    estimated_time: Optional[str] = None
    # --- KẾT THÚC THÊM MỚI ---
    
class LongTermGuestRead(LongTermGuestBase):
    id: int
    is_active: bool
    registered_by_user_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# SỬA LỖI: Thêm schema LongTermGuestReadWithUser (giữ nguyên)
class LongTermGuestReadWithUser(LongTermGuestRead):
    registered_by_name: Optional[str] = None
```

### 1.3. Cập nhật Router Khách (`backend/app/routers/guests.py`)

Cập nhật 3 hàm `create_guest`, `create_guests_bulk`, và `export_guests` để xử lý trường mới.

```python
# File: backend/app/routers/guests.py
# ... (các imports giữ nguyên)

@router.post("/", response_model=schemas.GuestRead, dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def create_guest(payload: schemas.GuestCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user), bg: BackgroundTasks = BackgroundTasks()):
    # ... (logic chuẩn hóa biển số và tên giữ nguyên)

    guest = models.Guest(
        full_name=standardized_full_name,
        id_card_number=payload.id_card_number or "",
        company=payload.company or "",
        reason=payload.reason or "",
        license_plate=payload.license_plate or "",
        supplier_name=payload.supplier_name or "",
        status="pending",
        # --- THÊM MỚI: Lưu Giờ dự kiến ---
        estimated_time=payload.estimated_time or "",
        # --- KẾT THÚC THÊM MỚI ---
        registered_by_user_id=user.id
    )
    # ... (logic commit và gửi thông báo giữ nguyên)

@router.post("/bulk", response_model=list[schemas.GuestRead], dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def create_guests_bulk(payload: schemas.GuestBulkCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user), bg: BackgroundTasks = BackgroundTasks()):
    # ... (logic chuẩn hóa biển số giữ nguyên)
    
    for individual in payload.guests:
        # ... (logic chuẩn hóa tên giữ nguyên)

        guest = models.Guest(
            full_name=standardized_individual_name,
            id_card_number=individual.id_card_number or "",
            company=payload.company or "",
            reason=payload.reason or "",
            license_plate=formatted_plate,
            supplier_name=payload.supplier_name or "",
            status="pending",
            # --- THÊM MỚI: Lưu Giờ dự kiến ---
            estimated_time=payload.estimated_time or "",
            # --- KẾT THÚC THÊM MỚI ---
            registered_by_user_id=user.id
        )
        # ... (logic commit và gửi thông báo giữ nguyên)

@router.put("/{guest_id}", response_model=schemas.GuestRead)
def update_guest(guest_id: int, payload: schemas.GuestUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # ... (logic kiểm tra quyền và lấy guest giữ nguyên)

    update_data = payload.model_dump(exclude_unset=True)

    # Chuẩn hóa biển số khi cập nhật (giữ nguyên)
    if 'license_plate' in update_data and update_data['license_plate']:
        update_data['license_plate'] = format_license_plate(update_data['license_plate'])

    # --- THÊM MỚI: Xử lý Estimated Time ---
    if 'estimated_time' in update_data and update_data['estimated_time'] is not None:
         # Lưu trực tiếp chuỗi HH:MM
        guest.estimated_time = update_data['estimated_time']
    # --- KẾT THÚC THÊM MỚI ---
    
    for field, value in update_data.items():
         # LƯU Ý: Nếu đã xử lý estimated_time ở trên, cần bỏ qua
         if field not in ('estimated_time'):
            setattr(guest, field, value)

    db.commit()
    db.refresh(guest)
    return guest

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin", "manager"))])
def export_guests(db: Session = Depends(get_db)):
    # ... (logic truy vấn giữ nguyên)

        data_to_export = []
        for guest, registered_by_name, registered_by_username in results:
            data_to_export.append({
                "Họ tên": guest.full_name,
                # ... (các cột khác giữ nguyên)
                "Ngày đăng ký": guest.created_at.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y %H:%M") if guest.created_at else "",
                "Trạng thái": "ĐÃ VÀO" if guest.status == 'checked_in' else "CHƯA VÀO",
                "Giờ vào": guest.check_in_time.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y %H:%M") if guest.check_in_time else "",
                # --- THÊM MỚI: Xuất Giờ dự kiến ---
                "Giờ dự kiến": guest.estimated_time,
                # --- KẾT THÚC THÊM MỚI ---
                "Lý do": guest.reason,
                "Hình ảnh": ", ".join([img.image_path for img in guest.images])
            })
    # ... (logic tạo và trả về file Excel giữ nguyên)
```

### 1.4. Cập nhật Router Khách Dài hạn (`backend/app/routers/long_term_guests.py`)

Thêm `estimated_time` vào quá trình tạo và cập nhật khách dài hạn, đồng thời đảm bảo nó được truyền xuống bản ghi `Guest` được tạo tức thì.

```python
# File: backend/app/routers/long_term_guests.py

@router.post("/", response_model=schemas.LongTermGuestRead)
def create_long_term_guest(
    payload: schemas.LongTermGuestCreate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    # ... (logic validation ngày giữ nguyên)

    db_long_term_guest = models.LongTermGuest(
        **payload.model_dump(),
        registered_by_user_id=user.id
    )
    db.add(db_long_term_guest)
    db.commit()

    # --- CẢI TIẾN: Đồng bộ logic chống trùng (Cập nhật thêm Estimated Time) ---
    today = get_local_time().date()
    if db_long_term_guest.start_date <= today <= db_long_term_guest.end_date:
        # ... (logic kiểm tra existing_guest giữ nguyên)

        if not existing_guest:
            guest_for_today = models.Guest(
                full_name=payload.full_name,
                id_card_number=payload.id_card_number or "",
                company=payload.company or "",
                reason=payload.reason or "",
                license_plate=payload.license_plate or "",
                supplier_name=payload.supplier_name or "",
                status="pending",
                # --- THÊM MỚI: Truyền Estimated Time ---
                estimated_time=payload.estimated_time or "",
                # --- KẾT THÚC THÊM MỚI ---
                registered_by_user_id=user.id,
                created_at=get_local_time()
            )
            db.add(guest_for_today)
            db.commit()

    db.refresh(db_long_term_guest)
    return db_long_term_guest
    
@router.put("/{guest_id}", response_model=schemas.LongTermGuestRead)
def update_long_term_guest(
    guest_id: int, 
    payload: schemas.LongTermGuestUpdate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    # ... (logic kiểm tra quyền và lấy db_guest giữ nguyên)

    update_data = payload.model_dump(exclude_unset=True)

    # ... (logic validate ngày giữ nguyên)
    
    # --- THÊM MỚI: Áp dụng Estimated Time từ update_data ---
    if 'estimated_time' in update_data and update_data['estimated_time'] is not None:
        db_guest.estimated_time = update_data['estimated_time']
    # --- KẾT THÚC THÊM MỚI ---

    for key, value in update_data.items():
        # LƯU Ý: Bỏ qua estimated_time nếu đã xử lý ở trên
        if key not in ('estimated_time'):
            setattr(db_guest, key, value)
        
    db.commit()
    db.refresh(db_guest)
    return db_guest
```

### 1.5. Cập nhật Logic Tự động tạo hàng ngày (`backend/app/main.py`)

Đảm bảo `estimated_time` được sao chép từ `LongTermGuest` sang `Guest` khi tác vụ nền chạy.

```python
# File: backend/app/main.py

# ... (các imports khác)
# ...
def create_daily_guest_entries():
    # ... (logic lấy now_tz và start_of_day, end_of_day giữ nguyên)

        active_long_term_guests = db.query(models.LongTermGuest).filter(
            # ... (logic filter giữ nguyên)
        ).all()

        created_count = 0
        for lt in active_long_term_guests:
            # ... (logic kiểm tra exists giữ nguyên)

            if not exists:
                new_guest = models.Guest(
                    full_name=lt.full_name,
                    id_card_number=lt.id_card_number,
                    company=getattr(lt, "company", None),
                    reason=f"Khách dài hạn: {lt.reason or ''}",
                    license_plate=lt.license_plate,
                    supplier_name=lt.supplier_name,
                    status="pending",
                    # --- THÊM MỚI: Truyền Estimated Time từ LongTermGuest ---
                    estimated_time=lt.estimated_time,
                    # --- KẾT THÚC THÊM MỚI ---
                    registered_by_user_id=lt.registered_by_user_id,
                    created_at=now_tz,
                )
                db.add(new_guest)
                created_count += 1
    # ... (logic commit và finally giữ nguyên)
```

### 1.6. Tích hợp vào Telegram Notifications (`backend/app/utils/notifications.py`)

Cập nhật các hàm định dạng để bao gồm trường **"Giờ dự kiến"**.

```python
# File: backend/app/utils/notifications.py

# ... (các imports và hàm khác giữ nguyên)

def format_pending_list_for_telegram(pending_guests: List[models.Guest]) -> str:
    """Định dạng danh sách khách đang chờ cho kênh chính."""
    # ... (logic lấy now giữ nguyên)

    if not pending_guests:
        return f"✅ <b>Tất cả khách đã được xác nhận vào.</b>\n<i>(Cập nhật lúc {now})</i>"

    # ... (logic header giữ nguyên)

    lines = [header]
    for i, guest in enumerate(pending_guests, 1):
        # ... (logic escape chuỗi giữ nguyên)
        plate = (guest.license_plate or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
        # --- THÊM MỚI: Giờ dự kiến ---
        estimated_time_str = (guest.estimated_time or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        # --- KẾT THÚC THÊM MỚI ---

        registered_by_name = guest.registered_by.full_name if guest.registered_by else "Không rõ"
        registered_by_name = registered_by_name.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        lines.append("--------------------")
        lines.append(f"{i} - <b>{full_name}</b> - {id_card}")
        lines.append(f"   Dự kiến: {estimated_time_str}") # <-- HIỂN THỊ TRƯỜNG MỚI
        lines.append(f"   BKS: {plate}")
        lines.append(f"   NCC: {supplier}")
        lines.append(f"   Người ĐK: {registered_by_name}")

    # ... (logic footer và giới hạn độ dài giữ nguyên)

def format_event_for_archive(guest: models.Guest, event_type: str, user_who_triggered: models.User) -> str:
    """Định dạng chi tiết sự kiện của khách cho kênh lưu trữ."""
    
    # ... (logic lấy event_title, event_icon, now_short giữ nguyên)

    # 3. Chuẩn bị & Escape dữ liệu
    # ... (logic escape chuỗi giữ nguyên)
    plate = (guest.license_plate or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    reason = (guest.reason or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # --- THÊM MỚI: Giờ dự kiến ---
    estimated_time_str = (guest.estimated_time or 'N/A').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    # --- KẾT THÚC THÊM MỚI ---

    # ... (logic lấy tên người đăng ký gốc và người kích hoạt giữ nguyên)

    # 4. Xây dựng tin nhắn
    lines = [
        f"{event_icon} <b>[SỰ KIỆN] {event_title}</b>",
        "",
        f"👤 <b>Khách:</b> {full_name} ({id_card})",
        f"⏰ <b>Dự kiến:</b> {estimated_time_str}", # <-- HIỂN THỊ TRƯỜNG MỚI
        f"📝 <b>Người ĐK:</b> {registered_by_original}",
        f"🚗 <b>BKS:</b> {plate}",
        # ... (các dòng khác giữ nguyên)
    ]
    # ... (logic dòng cuối và giới hạn độ dài giữ nguyên)
```

-----

## 2\. Thay đổi ở Frontend (UI & Logic Cảnh báo)

### 2.1. Trang Đăng ký Khách (`frontend/src/pages/RegisterGuest.vue`)

Thêm trường nhập giờ và cột hiển thị.

````vue
// File: frontend/src/pages/RegisterGuest.vue

// ... (các script setup imports giữ nguyên)

const initialFormState = {
  full_name: '', id_card_number: '', company: '', reason: '',
  license_plate: '', supplier_name: '',
  // --- THÊM MỚI: Estimated Time ---
  estimated_time: '',
  // --- KẾT THÚC THÊM MỚI ---
  guests: [{ full_name: '', id_card_number: '' }]
}
// ... (các refs và reactive objects giữ nguyên)

const columns = [
  // ... (các cột giữ nguyên)
  { name: 'license_plate', align: 'left', label: 'Biển số', field: 'license_plate', sortable: true },
  // --- THÊM MỚI: Cột Giờ dự kiến ---
  { name: 'estimated_time', align: 'left', label: 'Dự kiến', field: 'estimated_time', sortable: true },
  // --- KẾT THÚC THÊM MỚI ---
  { name: 'registered_by_name', align: 'left', label: 'Người đăng ký', field: 'registered_by_name', sortable: true },
  // ... (các cột khác giữ nguyên)
]

// ... (trong template)

          <div v-else class="row q-col-gutter-md">
            <div class="col-12 col-md-4"><q-input v-model="form.full_name" label="Họ tên" dense outlined required /></div>
            <div class="col-12 col-md-4"><q-input v-model="form.id_card_number" label="CCCD" dense outlined /></div>
            
            <div class="col-12 col-md-4">
                 <q-input v-model="form.estimated_time" label="Giờ dự kiến" dense outlined type="time" mask="time" hint="HH:MM">
                    <template v-slot:append>
                        <q-icon name="schedule" class="cursor-pointer" />
                    </template>
                 </q-input>
            </div>
            <div class="col-12 col-md-6">
              </div>
            <div class="col-12 col-md-6">
              </div>
            <div class="col-12"><q-input type="textarea" v-model="form.reason" label="Chi tiết" outlined dense /></div>
          </div>
          
          <q-input v-model="editForm.id_card_number" label="CCCD" dense outlined />
          
          <q-input v-model="editForm.estimated_time" label="Giờ dự kiến" dense outlined type="time" mask="time" hint="HH:MM">
            <template v-slot:append>
                <q-icon name="schedule" class="cursor-pointer" />
            </template>
          </q-input>
          ```

### 2.2. Trang Cổng Bảo Vệ (`frontend/src/pages/GuardGate.vue`)

Thêm logic kiểm tra **quá giờ dự kiến** (dựa trên giờ client) và bôi đỏ hàng.

```vue
// File: frontend/src/pages/GuardGate.vue

// ... (các script setup imports giữ nguyên)

// --- Logic tính toán thời gian ---
function isOverdue(row) {
    if (!row.estimated_time || row.status !== 'pending') return false;
    
    // Server/Client Time is sufficient for UI alert
    const now = new Date();
    const [estHour, estMin] = row.estimated_time.split(':').map(Number);
    
    const estDate = new Date(now.getFullYear(), now.getMonth(), now.getDate(), estHour, estMin, 0);

    return now > estDate;
}

// --- ĐỊNH NGHĨA CỘT MỚI ---
const baseColumns = [
  { name: 'full_name', align: 'left', label: 'Họ tên', field: 'full_name', sortable: true },
  { name: 'id_card_number', align: 'left', label: 'CCCD', field: 'id_card_number', sortable: true },
  { name: 'supplier_name', align: 'left', label: 'Nhà cung cấp', field: 'supplier_name', sortable: true },
  { name: 'reason', align: 'left', label: 'Chi tiết', field: 'reason', sortable: true, style: 'max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;' },
  { name: 'license_plate', align: 'left', label: 'Biển số', field: 'license_plate', sortable: true },
  // --- THÊM MỚI: Giờ dự kiến ---
  { name: 'estimated_time', align: 'left', label: 'Dự kiến', field: 'estimated_time', sortable: true },
  // --- KẾT THÚC THÊM MỚI ---
  { name: 'registered_by_name', align: 'left', label: 'Người đăng ký', field: 'registered_by_name', sortable: true },
  { name: 'created_at', align: 'left', label: 'Ngày đăng ký', field: 'created_at', sortable: true, format: val => val ? new Date(val).toLocaleString('vi-VN') : '' },
];

const pendingColumns = [
  // Cột "actions" được đưa lên đầu tiên
  { name: 'actions', label: 'Hành động', field: 'actions', align: 'left' },
  ...baseColumns
];
// ... (checkedInColumns giữ nguyên)

// ... (trong template)
      <q-table
        :rows="pending"
        :columns="pendingColumns"
        row-key="id"
        flat
        :pagination="{ rowsPerPage: 20 }"
        :loading="loading"
        >
        
        <template #body-cell="props">
            <q-td 
                :props="props" 
                :class="{'text-red-9 text-bold bg-red-1': isOverdue(props.row) }"
                >
                {{ props.value }}
            </q-td>
        </template>
        <template #body-cell-actions="props">
            </template>
        <template #no-data>
            </template>
      </q-table>
// ... (trong setup cuối cùng, cần expose isOverdue)
// export function isOverdue (row) is a good utility, but since is used in template:
// return { ..., isOverdue }; in original code:
// const $q = useQuasar() ...

// You need to expose isOverdue to the template for it to work on the row:

/*
// This is not standard Vue 3 composition API practice, but since the original code 
// didn't define a setup function for `setup` inside a <script setup> block, 
// I must assume that the provided code is incomplete or a custom setup. 
// Since isOverdue is a local function inside <script setup>, it should be accessible.
// The primary issue might be that :class in Quasar q-table body-cell applies to all cells.
// The provided Vue code snippet seems to be a composition API script block.
// I will ensure that the isOverdue function is callable by the template (which it is in <script setup>)
// and that the logic correctly applies to the entire row.
*/

// No need to export explicitly in script setup, it's accessible.
// The logic is implemented via the custom #body-cell template.
// Everything looks good.
````

### 2.3. Trang Khách Dài hạn (`frontend/src/pages/LongTermGuestsPage.vue`)

Cập nhật giao diện chỉnh sửa để bao gồm trường Giờ dự kiến.

````vue
// File: frontend/src/pages/LongTermGuestsPage.vue

// ... (các script setup imports giữ nguyên)

const editForm = reactive({
  // ... (các trường giữ nguyên)
  license_plate: '',
  reason: '',
  // --- THÊM MỚI: Giờ dự kiến ---
  estimated_time: '',
  // --- KẾT THÚC THÊM MỚI ---
  start_date_display: '',
  end_date_display: ''
});

// ... (trong openEditDialog)
function openEditDialog(row) {
  Object.assign(editForm, row);
  // CẢI TIẾN: Chuẩn hoá format ngày để hiển thị
  editForm.start_date_display = quasarDate.formatDate(row.start_date, 'YYYY/MM/DD');
  editForm.end_date_display = quasarDate.formatDate(row.end_date, 'YYYY/MM/DD');
  showEditDialog.value = true;
}

// ... (trong onUpdateSubmit)
async function onUpdateSubmit() {
  try {
    // ... (logic lấy start/end date giữ nguyên)
    
    const payload = {
      full_name: editForm.full_name,
      // ... (các trường khác giữ nguyên)
      license_plate: editForm.license_plate,
      reason: editForm.reason,
      start_date: quasarDate.formatDate(startDate, 'YYYY-MM-DD'),
      end_date: quasarDate.formatDate(endDate, 'YYYY-MM-DD'),
      // --- THÊM MỚI: Gửi Estimated Time ---
      estimated_time: editForm.estimated_time
      // --- KẾT THÚC THÊM MỚI ---
    };

    await api.put(`/long-term-guests/${editForm.id}`, payload);
    // ... (logic notify và loadData giữ nguyên)
  } catch (error) {
    // ... (logic error giữ nguyên)
  }
}

// ... (trong template)
            <q-input v-model="editForm.license_plate" label="Biển số" dense outlined />
            
            <q-input v-model="editForm.estimated_time" label="Giờ dự kiến" dense outlined type="time" mask="time" hint="HH:MM">
               <template v-slot:append>
                    <q-icon name="schedule" class="cursor-pointer" />
                </template>
            </q-input>
            <q-input type="textarea" v-model="editForm.reason" label="Chi tiết" outlined dense />
            
            ```
````