# File: backend/app/routers/guests.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, func
from datetime import datetime
import pandas as pd
import io
import logging
import uuid
import os
from typing import List

from .. import models, schemas
from ..deps import get_db
from ..auth import get_current_user, require_roles
from ..models import get_local_time
from ..config import settings
from ..database import unaccent_string
# Cập nhật import: Thêm hàm gửi sự kiện lưu trữ
from ..utils.notifications import run_pending_list_notification, send_event_to_archive_background
from ..utils.plate_formatter import format_license_plate

router = APIRouter(prefix="/guests", tags=["guests"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.GuestRead, dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def create_guest(payload: schemas.GuestCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user), bg: BackgroundTasks = BackgroundTasks()):
    """
    Tạo một bản ghi khách lẻ mới.
    """
    # Chuẩn hóa biển số ngay khi nhận được yêu cầu
    if payload.license_plate:
        payload.license_plate = format_license_plate(payload.license_plate)

    guest = models.Guest(
        full_name=payload.full_name,
        id_card_number=payload.id_card_number or "",
        company=payload.company or "",
        reason=payload.reason or "",
        license_plate=payload.license_plate or "",
        supplier_name=payload.supplier_name or "",
        status="pending",
        registered_by_user_id=user.id
    )
    db.add(guest)
    db.commit()
    db.refresh(guest) # Cần refresh để lấy guest.id

    # --- THÊM MỚI: Gửi sự kiện đăng ký mới đến kênh lưu trữ ---
    # Gửi id của khách và người dùng hiện tại
    bg.add_task(send_event_to_archive_background, guest.id, "Đăng ký mới", user.id)
    # --- KẾT THÚC THÊM MỚI ---

    # Kích hoạt cập nhật danh sách chờ trên kênh chính
    bg.add_task(run_pending_list_notification)

    return guest

@router.post("/{guest_id}/upload-image", response_model=schemas.GuestImageRead, dependencies=[Depends(require_roles("admin", "manager", "staff"))])
async def upload_guest_image(guest_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    # Logic tải ảnh giữ nguyên
    guest = db.query(models.Guest).get(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")

    try:
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"

        save_path = os.path.join(settings.UPLOAD_DIR, "guests", unique_filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, "wb") as buffer:
            buffer.write(await file.read())

        db_image = models.GuestImage(
            guest_id=guest_id,
            image_path=f"guests/{unique_filename}"
        )
        db.add(db_image)
        db.commit()
        db.refresh(db_image)

        return db_image
    except Exception as e:
        logger.error(f"Could not upload image for guest {guest_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not upload image")

@router.post("/bulk", response_model=list[schemas.GuestRead], dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def create_guests_bulk(payload: schemas.GuestBulkCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user), bg: BackgroundTasks = BackgroundTasks()):
    new_guests_db = [] # Lưu các đối tượng Guest sau khi commit

    # Chuẩn hóa biển số cho cả đoàn
    formatted_plate = format_license_plate(payload.license_plate) if payload.license_plate else ""

    for individual in payload.guests:
        if not individual.full_name:
            continue
        guest = models.Guest(
            full_name=individual.full_name,
            id_card_number=individual.id_card_number or "",
            company=payload.company or "",
            reason=payload.reason or "",
            license_plate=formatted_plate,
            supplier_name=payload.supplier_name or "",
            status="pending",
            registered_by_user_id=user.id
        )
        db.add(guest)
        # Lưu tạm thời để gửi thông báo sau khi commit
        new_guests_db.append(guest)

    if not new_guests_db:
        raise HTTPException(status_code=400, detail="No valid guests to add.")

    db.commit() # Commit tất cả khách mới

    # --- THÊM MỚI: Gửi sự kiện lưu trữ cho từng khách trong đoàn ---
    for guest in new_guests_db:
        db.refresh(guest) # Cần refresh để lấy guest.id
        bg.add_task(send_event_to_archive_background, guest.id, "Đăng ký mới (theo đoàn)", user.id)
    # --- KẾT THÚC THÊM MỚI ---

    # Kích hoạt cập nhật kênh chính (chỉ 1 lần sau khi thêm cả đoàn)
    bg.add_task(run_pending_list_notification)

    # Trả về danh sách khách đã tạo (cần refresh lại để có id)
    return new_guests_db

@router.get("/", response_model=list[schemas.GuestReadWithUser])
def list_guests(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
    q: str | None = Query(default=None, description="Tìm kiếm tương đối"),
    include_all_my_history: bool = False
):
    # Logic truy vấn và trả về danh sách giữ nguyên
    query = db.query(
        models.Guest,
        models.User.full_name.label("registered_by_name")
    ).join(
        models.User, models.Guest.registered_by_user_id == models.User.id
    ).options(joinedload(models.Guest.images)) # Thêm joinedload để lấy ảnh

    if user.role == "staff":
        query = query.filter(models.Guest.registered_by_user_id == user.id)
        if not include_all_my_history:
            query = query.filter(models.Guest.status == "pending")

    if q:
        unaccented_q = unaccent_string(q)
        like = f"%{unaccented_q}%"

        query = query.filter(or_(
            func.unaccent(models.Guest.full_name).ilike(like),
            models.Guest.id_card_number.ilike(like),
            func.unaccent(models.Guest.company).ilike(like),
            func.unaccent(models.Guest.reason).ilike(like),
            models.Guest.license_plate.ilike(like), # Biển số đã chuẩn hóa, tìm trực tiếp
            func.unaccent(models.Guest.supplier_name).ilike(like),
            func.unaccent(models.User.full_name).ilike(like),
            models.Guest.status.ilike(f"%{q}%") # Giữ lại tìm kiếm status gốc
        ))

    results = query.order_by(models.Guest.created_at.desc()).all()

    # Đảm bảo trả về cả thông tin ảnh
    output = []
    for guest, registered_by_name in results:
        guest_data = schemas.GuestRead.model_validate(guest).model_dump()
        guest_data["registered_by_name"] = registered_by_name
        guest_data["images"] = [schemas.GuestImageRead.model_validate(img) for img in guest.images]
        output.append(schemas.GuestReadWithUser.model_validate(guest_data))

    return output

@router.get("/suggestions", response_model=schemas.GuestSuggestions)
def get_suggestions(db: Session = Depends(get_db)):
    # Logic gợi ý giữ nguyên
    license_plates = db.query(models.Guest.license_plate).filter(models.Guest.license_plate != "").distinct().all()
    supplier_names = db.query(models.Guest.supplier_name).filter(models.Guest.supplier_name != "").distinct().all()
    return {
        "companies": [], # Bỏ gợi ý company nếu không cần
        "license_plates": [lp[0] for lp in license_plates if lp[0]],
        "supplier_names": [sn[0] for sn in supplier_names if sn[0]]
    }

@router.put("/{guest_id}", response_model=schemas.GuestRead)
def update_guest(guest_id: int, payload: schemas.GuestUpdate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Logic cập nhật giữ nguyên, bao gồm chuẩn hóa biển số
    guest = db.query(models.Guest).get(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    if user.role == "staff" and guest.registered_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    update_data = payload.model_dump(exclude_unset=True)

    # Chuẩn hóa biển số khi cập nhật
    if 'license_plate' in update_data and update_data['license_plate']:
        update_data['license_plate'] = format_license_plate(update_data['license_plate'])

    for field, value in update_data.items():
        setattr(guest, field, value)

    db.commit()
    db.refresh(guest)
    return guest

def _archive_image(image_path: str):
    # Logic lưu trữ ảnh giữ nguyên
    try:
        archive_dir = os.path.join(settings.UPLOAD_DIR, "archived_guests")
        os.makedirs(archive_dir, exist_ok=True)

        source_path = os.path.join(settings.UPLOAD_DIR, image_path)
        if os.path.exists(source_path):
            file_name = os.path.basename(image_path)
            dest_path = os.path.join(archive_dir, file_name)
            # Sửa lỗi tiềm ẩn nếu file đích đã tồn tại
            if os.path.exists(dest_path):
                 dest_path = os.path.join(archive_dir, f"{uuid.uuid4()}_{file_name}")
            os.rename(source_path, dest_path)
            logger.info(f"Archived image from {source_path} to {dest_path}")
    except Exception as e:
        logger.error(f"Could not archive image file {image_path}: {e}")

@router.delete("/{guest_id}")
def delete_guest(guest_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Logic xóa giữ nguyên
    guest = db.query(models.Guest).options(joinedload(models.Guest.images)).get(guest_id)
    if not guest:
        raise HTTPException(status_code=404, detail="Guest not found")
    if user.role not in ("admin", "manager") and not (user.role == "staff" and guest.registered_by_user_id == user.id):
        raise HTTPException(status_code=403, detail="Not allowed")

    for image in guest.images:
        _archive_image(image.image_path)

    db.delete(guest)
    db.commit()
    return {"ok": True}

@router.delete("/images/{image_id}", dependencies=[Depends(require_roles("admin", "manager", "staff"))])
def delete_guest_image(image_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Logic xóa ảnh giữ nguyên
    logger.info(f"User {user.username} attempting to delete image {image_id}")
    db_image = db.query(models.GuestImage).options(joinedload(models.GuestImage.guest)).get(image_id)

    if not db_image:
        logger.warning(f"Image {image_id} not found.")
        raise HTTPException(status_code=404, detail="Image not found")

    guest = db_image.guest
    if not guest:
        logger.error(f"Image {image_id} has no associated guest.")
        raise HTTPException(status_code=500, detail="Image is orphaned")

    is_admin_or_manager = user.role in ("admin", "manager")
    is_owner = guest.registered_by_user_id == user.id

    if not (is_admin_or_manager or is_owner):
        logger.warning(f"User {user.username} does not have permission to delete image {image_id} for guest {guest.id}")
        raise HTTPException(status_code=403, detail="Not allowed to delete this image")

    logger.info(f"Permission granted. Archiving image {db_image.image_path}")
    _archive_image(db_image.image_path)

    logger.info(f"Deleting image record {image_id} from database.")
    db.delete(db_image)
    db.commit()

    logger.info(f"Successfully deleted image {image_id}.")
    return {"ok": True}

@router.post("/import/xlsx", dependencies=[Depends(require_roles("admin", "manager"))])
def import_guests(file: UploadFile = File(...), db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Logic import giữ nguyên
    try:
        # Sử dụng BytesIO để đọc file trực tiếp từ memory
        content = file.file.read()
        df = pd.read_excel(io.BytesIO(content), keep_default_na=False)
        df.dropna(how='all', inplace=True)

        users_cache = {u.username: u for u in db.query(models.User).all()}
        imported_count = 0

        for index, row in df.iterrows():
            if not row.get("Họ tên"):
                logger.warning(f"Bỏ qua dòng {index + 2}: Thiếu họ tên.")
                continue

            status_str = str(row.get("Trạng thái", "")).strip()
            status = "checked_in" if status_str == "ĐÃ VÀO" else "pending"

            check_in_time = None
            if status == "checked_in" and row.get("Giờ vào"):
                try:
                    time_val = row.get("Giờ vào")
                    if isinstance(time_val, datetime):
                        check_in_time = time_val
                    else:
                        # Thử các định dạng phổ biến hơn
                        for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M"):
                             try:
                                 check_in_time = datetime.strptime(str(time_val), fmt)
                                 break
                             except ValueError:
                                 continue
                        if not check_in_time:
                             logger.warning(f"Không thể phân tích 'Giờ vào' '{time_val}' cho '{row.get('Họ tên')}' ở dòng {index+2}. Dùng giờ hiện tại.")
                             # Hoặc đặt là None nếu không muốn mặc định giờ hiện tại
                             # check_in_time = get_local_time()
                except Exception as e:
                    logger.warning(f"Lỗi khi xử lý 'Giờ vào' '{row.get('Giờ vào')}' cho '{row.get('Họ tên')}' ở dòng {index+2}. Lỗi: {e}")

            registered_by_user_id = user.id
            registered_by_username = str(row.get("Mã NV đăng ký", "")).strip()
            if registered_by_username in users_cache:
                registered_by_user_id = users_cache[registered_by_username].id
            else:
                 logger.warning(f"Không tìm thấy username '{registered_by_username}' ở dòng {index+2}. Gán khách '{row.get('Họ tên')}' cho người import '{user.username}'.")

            license_plate_raw = row.get("Biển số", "")

            guest = models.Guest(
                full_name=row.get("Họ tên", ""),
                id_card_number=str(row.get("CCCD", "")),
                supplier_name=row.get("Nhà cung cấp", row.get("Công ty", "")), # Ưu tiên Nhà cung cấp
                company=row.get("Công ty", ""), # Vẫn giữ cột Công ty nếu có
                reason=row.get("Lý do", ""),
                license_plate=format_license_plate(license_plate_raw) if license_plate_raw else "",
                status=status,
                check_in_time=check_in_time,
                registered_by_user_id=registered_by_user_id
            )

            image_paths_str = row.get("Hình ảnh", "")
            if image_paths_str and isinstance(image_paths_str, str):
                image_paths = [path.strip() for path in image_paths_str.split(',') if path.strip()]
                for path in image_paths:
                    if not path.startswith("guests/"): continue # Bỏ qua nếu đường dẫn không hợp lệ

                    full_path = os.path.join(settings.UPLOAD_DIR, path)
                    base_name = os.path.basename(path)
                    archived_path = os.path.join(settings.UPLOAD_DIR, "archived_guests", base_name)

                    # Khôi phục ảnh nếu nó nằm trong kho lưu trữ
                    if not os.path.exists(full_path) and os.path.exists(archived_path):
                        try:
                            os.rename(archived_path, full_path)
                            logger.info(f"Khôi phục ảnh lưu trữ từ {archived_path} về {full_path}")
                        except Exception as e:
                            logger.error(f"Không thể khôi phục ảnh {base_name}: {e}")

                    # Tạo lại liên kết trong CSDL nếu file tồn tại
                    if os.path.exists(full_path):
                        image_record = models.GuestImage(image_path=path)
                        guest.images.append(image_record)
                    else:
                        logger.warning(f"Đường dẫn ảnh '{path}' được liệt kê trong file import nhưng không tìm thấy file.")

            db.add(guest)
            imported_count += 1

        db.commit()
        return {"ok": True, "message": f"Import thành công {imported_count} bản ghi."}
    except Exception as e:
        db.rollback()
        logger.error(f"Xử lý file thất bại: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Xử lý file thất bại: {e}")

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin", "manager"))])
def export_guests(db: Session = Depends(get_db)):
    # Logic export giữ nguyên
    try:
        results = db.query(
            models.Guest,
            models.User.full_name.label("registered_by_name"),
            models.User.username.label("registered_by_username")
        ).join(
            models.User, models.Guest.registered_by_user_id == models.User.id
        ).options(joinedload(models.Guest.images)).order_by(models.Guest.created_at.desc()).all()

        data_to_export = []
        for guest, registered_by_name, registered_by_username in results:
            data_to_export.append({
                "Họ tên": guest.full_name,
                "CCCD": guest.id_card_number,
                "Nhà cung cấp": guest.supplier_name,
                "Công ty": guest.company, # Thêm cột Công ty
                "Biển số": guest.license_plate,
                "Người đăng ký": registered_by_name,
                "Mã NV đăng ký": registered_by_username,
                "Ngày đăng ký": guest.created_at.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y %H:%M") if guest.created_at else "",
                "Trạng thái": "ĐÃ VÀO" if guest.status == 'checked_in' else "CHƯA VÀO",
                "Giờ vào": guest.check_in_time.astimezone(pytz.timezone(settings.TZ)).strftime("%d/%m/%Y %H:%M") if guest.check_in_time else "",
                "Lý do": guest.reason,
                "Hình ảnh": ", ".join([img.image_path for img in guest.images])
            })

        df = pd.DataFrame(data_to_export)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: # Dùng xlsxwriter để auto-fit
            df.to_excel(writer, index=False, sheet_name='Guests')
            # Auto-adjust columns' width
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                writer.sheets['Guests'].set_column(col_idx, col_idx, column_width + 1) # Thêm chút padding

        output.seek(0)

        headers = {
            'Content-Disposition': f'attachment; filename="guests_export_{get_local_time().strftime("%Y%m%d_%H%M")}.xlsx"'
        }
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    except Exception as e:
        logger.error(f"Không thể tạo file Excel: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Không thể tạo file Excel.")

@router.post("/clear", dependencies=[Depends(require_roles("admin"))])
def clear_guests(db: Session = Depends(get_db)):
    # Logic xóa dữ liệu giữ nguyên
    try:
        all_images = db.query(models.GuestImage).all()
        for image in all_images:
            _archive_image(image.image_path) # Lưu trữ ảnh trước khi xóa bản ghi

        db.query(models.GuestImage).delete()
        db.query(models.Guest).delete()
        db.commit()
        return {"ok": True, "message": "Đã xóa toàn bộ dữ liệu khách và lưu trữ ảnh."}
    except Exception as e:
        db.rollback()
        logger.error(f"Lỗi khi xóa dữ liệu khách: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Xóa dữ liệu thất bại: {e}")
