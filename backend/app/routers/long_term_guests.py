# File: backend/app/routers/long_term_guests.py
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import date
from typing import List

from .. import models, schemas
from ..deps import get_db
from ..auth import get_current_user
from ..models import get_local_time

router = APIRouter(prefix="/long-term-guests", tags=["long-term-guests"])

@router.post("/", response_model=schemas.LongTermGuestRead)
def create_long_term_guest(
    payload: schemas.LongTermGuestCreate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    # Validate start and end dates
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="End date cannot be earlier than start date.")

    db_long_term_guest = models.LongTermGuest(
        **payload.model_dump(),
        registered_by_user_id=user.id
    )
    db.add(db_long_term_guest)
    db.commit()

    # --- CẢI TIẾN: Đồng bộ logic chống trùng ---
    # Ngay khi tạo, kiểm tra và tạo một bản ghi Guest cho ngày hôm nay nếu cần
    today = get_local_time().date()
    if db_long_term_guest.start_date <= today <= db_long_term_guest.end_date:
        existing_guest = db.query(models.Guest).filter(
            models.Guest.full_name == payload.full_name,
            models.Guest.id_card_number == (payload.id_card_number or ""),
            func.date(models.Guest.created_at) == today,
            models.Guest.registered_by_user_id == user.id
        ).first()

        if not existing_guest:
            guest_for_today = models.Guest(
                full_name=payload.full_name,
                id_card_number=payload.id_card_number or "",
                company=payload.company or "",
                reason=payload.reason or "",
                license_plate=payload.license_plate or "",
                supplier_name=payload.supplier_name or "",
                status="pending",
                registered_by_user_id=user.id,
                created_at=get_local_time() # Ghi nhận thời gian tạo thực tế
            )
            db.add(guest_for_today)
            db.commit()

    db.refresh(db_long_term_guest)
    return db_long_term_guest

@router.get("/", response_model=List[schemas.LongTermGuestReadWithUser])
def get_long_term_guests(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    query = db.query(models.LongTermGuest).options(joinedload(models.LongTermGuest.registered_by))
    if user.role == 'staff':
        query = query.filter(models.LongTermGuest.registered_by_user_id == user.id)
    
    results = query.order_by(models.LongTermGuest.created_at.desc()).all()
    
    # Manually construct response to include user info
    response_data = []
    for item in results:
        data = schemas.LongTermGuestRead.model_validate(item).model_dump()
        data['registered_by_name'] = item.registered_by.full_name if item.registered_by else 'N/A'
        response_data.append(data)
        
    return response_data
    
@router.put("/{guest_id}", response_model=schemas.LongTermGuestRead)
def update_long_term_guest(
    guest_id: int, 
    payload: schemas.LongTermGuestUpdate, 
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    db_guest = db.query(models.LongTermGuest).get(guest_id)
    if not db_guest:
        raise HTTPException(status_code=404, detail="Long-term guest not found")
    if user.role == 'staff' and db_guest.registered_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    update_data = payload.model_dump(exclude_unset=True)

    # --- CẢI TIẾN: Bổ sung validate ở PUT ---
    start_date = update_data.get('start_date', db_guest.start_date)
    end_date = update_data.get('end_date', db_guest.end_date)
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="End date cannot be earlier than start date.")

    for key, value in update_data.items():
        setattr(db_guest, key, value)
        
    db.commit()
    db.refresh(db_guest)
    return db_guest

@router.delete("/{guest_id}", status_code=204)
def delete_long_term_guest(
    guest_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    db_guest = db.query(models.LongTermGuest).get(guest_id)
    if not db_guest:
        raise HTTPException(status_code=404, detail="Long-term guest not found")
    if user.role not in ('admin', 'manager') and db_guest.registered_by_user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db.delete(db_guest)
    db.commit()
    return Response(status_code=204)

