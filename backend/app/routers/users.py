# File: security_mgmt_dev/backend/app/routers/users.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import pandas as pd
import io, logging
from datetime import datetime

from .. import models, schemas, config
from ..deps import get_db
from ..auth import get_password_hash, require_roles
from ..database import unaccent_string # <-- Import hàm unaccent

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.UserRead, dependencies=[Depends(require_roles("admin"))])
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = models.User(username=payload.username, password_hash=get_password_hash(payload.password),
                       full_name=payload.full_name, role=payload.role)
    db.add(user); db.commit(); db.refresh(user)
    return user

@router.get("/", response_model=list[schemas.UserRead], dependencies=[Depends(require_roles("admin", "manager"))])
def list_users(db: Session = Depends(get_db), q: str | None = Query(default=None, description="search")):
    query = db.query(models.User)
    if q:
        unaccented_q = unaccent_string(q)
        like = f"%{unaccented_q}%"
        query = query.filter(or_(
            models.User.username.ilike(like), 
            func.unaccent(models.User.full_name).ilike(like), 
            models.User.role.ilike(like)
        ))
    return query.order_by(models.User.created_at.desc()).all()

@router.put("/{user_id}", response_model=schemas.UserRead, dependencies=[Depends(require_roles("admin"))])
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.username and payload.username != user.username:
        if db.query(models.User).filter(models.User.username == payload.username).first():
            raise HTTPException(status_code=400, detail="New username already exists")
        user.username = payload.username

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.password is not None and payload.password.strip():
        user.password_hash = get_password_hash(payload.password)

    db.commit(); db.refresh(user); return user

@router.delete("/{user_id}", dependencies=[Depends(require_roles("admin"))])
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Add protection for admin user
    if user.username == config.settings.ADMIN_USERNAME:
        raise HTTPException(status_code=403, detail="Cannot delete the default admin user.")
    db.delete(user); db.commit(); return {"ok": True}

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin"))])
def export_users(db: Session = Depends(get_db)):
    try:
        users = db.query(models.User).all()
        data_to_export = [
            {
                "username": user.username,
                "full_name": user.full_name,
                "role": user.role,
                "password_hash": user.password_hash,
                "password": "" 
            }
            for user in users
        ]
        
        df = pd.DataFrame(data_to_export)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Users')
        
        output.seek(0)
        
        headers = {
            'Content-Disposition': f'attachment; filename="users_export_{datetime.now().strftime("%Y%m%d")}.xlsx"'
        }
        return Response(content=output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

    except Exception as e:
        logger.error(f"Could not generate users Excel file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not generate Excel file.")

@router.post("/clear", dependencies=[Depends(require_roles("admin"))])
def clear_users(db: Session = Depends(get_db)):
    try:
        # Delete all users except the admin
        num_deleted = db.query(models.User).filter(models.User.username != config.settings.ADMIN_USERNAME).delete()
        db.commit()
        return {"ok": True, "num_deleted": num_deleted}
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not clear users.")

@router.post("/import/xlsx", dependencies=[Depends(require_roles("admin"))])
async def import_users(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        df = pd.read_excel(io.BytesIO(await file.read()), keep_default_na=False)
        df.dropna(how='all', inplace=True)

        imported_count = 0
        for index, row in df.iterrows():
            try:
                username = str(row.get("username", "")).strip()
                full_name = str(row.get("full_name", "")).strip()
                role = str(row.get("role", "")).strip()
                
                if not all([username, full_name, role]):
                    logger.warning(f"Skipping row {index + 2} due to missing data.")
                    continue
                
                # Prevent re-importing admin
                if username == config.settings.ADMIN_USERNAME:
                    logger.warning(f"Skipping row {index + 2}: cannot import the default admin user.")
                    continue

                if db.query(models.User).filter(models.User.username == username).first():
                    logger.warning(f"Skipping row {index + 2}: user '{username}' already exists.")
                    continue

                password_hash = str(row.get("password_hash", "")).strip()
                password = str(row.get("password", "")).strip()

                final_hash = ""
                if password_hash:
                    final_hash = password_hash
                elif password:
                    final_hash = get_password_hash(password)
                else:
                    logger.warning(f"Skipping row {index + 2} for user '{username}': no password or password_hash provided.")
                    continue

                user = models.User(
                    username=username,
                    full_name=full_name,
                    role=role,
                    password_hash=final_hash
                )
                db.add(user)
                imported_count += 1
            except Exception as e:
                logger.error(f"Failed to process row {index + 2}: {e}")
        db.commit()
        return {"ok": True, "imported_count": imported_count}
    except Exception as e:
        db.rollback()
        logger.error(f"Error importing users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to import file: {e}")
