# File: security_mgmt_dev/backend/app/routers/suppliers.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
import pandas as pd
import io
import logging

from .. import models, schemas
from ..deps import get_db
from ..auth import require_roles

router = APIRouter(prefix="/suppliers", tags=["suppliers"], dependencies=[Depends(require_roles("admin", "manager"))])
logger = logging.getLogger(__name__)

@router.post("/", response_model=schemas.SupplierRead)
def create_supplier(payload: schemas.SupplierCreate, db: Session = Depends(get_db)):
    if db.query(models.Supplier).filter(models.Supplier.name == payload.name).first():
        raise HTTPException(status_code=400, detail="Supplier exists")
    s = models.Supplier(name=payload.name)
    db.add(s); db.commit(); db.refresh(s)
    return s

@router.get("/", response_model=list[schemas.SupplierRead])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(models.Supplier).all()

@router.put("/{supplier_id}", response_model=schemas.SupplierRead)
def update_supplier(supplier_id: int, payload: schemas.SupplierUpdate, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    if payload.name is not None:
        s.name = payload.name
    db.commit(); db.refresh(s); return s

@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    db.delete(s); db.commit(); return {"ok": True}

@router.post("/{supplier_id}/plates", response_model=schemas.SupplierPlateRead)
def add_plate(supplier_id: int, payload: schemas.SupplierPlateCreate, db: Session = Depends(get_db)):
    s = db.query(models.Supplier).get(supplier_id)
    if not s:
        raise HTTPException(status_code=404, detail="Supplier not found")
    p = models.SupplierPlate(supplier_id=supplier_id, plate=payload.plate.upper())
    db.add(p); db.commit(); db.refresh(p); return p

@router.get("/{supplier_id}/plates", response_model=list[schemas.SupplierPlateRead])
def list_plates(supplier_id: int, db: Session = Depends(get_db)):
    return db.query(models.SupplierPlate).filter_by(supplier_id=supplier_id).all()

@router.delete("/{supplier_id}/plates/{plate_id}")
def delete_plate(supplier_id: int, plate_id: int, db: Session = Depends(get_db)):
    p = db.query(models.SupplierPlate).get(plate_id)
    if not p or p.supplier_id != supplier_id:
        raise HTTPException(status_code=404, detail="Plate not found")
    db.delete(p); db.commit(); return {"ok": True}

@router.get("/export/xlsx", dependencies=[Depends(require_roles("admin", "manager"))])
def export_suppliers(db: Session = Depends(get_db)):
    df = pd.read_sql(db.query(models.Supplier).statement, db.bind)
    bio = io.BytesIO()
    df.to_excel(bio, index=False, sheet_name="suppliers")
    bio.seek(0)
    headers = {"Content-Disposition": "attachment; filename=suppliers_export.xlsx"}
    return Response(bio.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers=headers)

@router.post("/import/xlsx", dependencies=[Depends(require_roles("admin"))])
async def import_suppliers(db: Session = Depends(get_db), file: UploadFile = File(...)):
    try:
        df = pd.read_excel(await file.read()).fillna('')
    except Exception as e:
        logger.error(f"Failed to read Excel file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid Excel file: {e}")
    
    for _, row in df.iterrows():
        try:
            if not row.get("name"):
                logger.warning(f"Skipping row due to missing name: {row.to_dict()}")
                continue
            if not db.query(models.Supplier).filter_by(name=row["name"]).first():
                db.add(models.Supplier(name=row["name"]))
        except Exception as e:
            logger.error(f"Failed to process row for supplier import: {row.to_dict()}", exc_info=True)
            continue
            
    db.commit()
    return {"ok": True}

@router.post("/clear", dependencies=[Depends(require_roles("admin"))])
def clear_suppliers(db: Session = Depends(get_db)):
    try:
        db.query(models.SupplierPlate).delete(synchronize_session=False)
        db.query(models.Supplier).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear suppliers: {e}")
    return {"ok": True}
