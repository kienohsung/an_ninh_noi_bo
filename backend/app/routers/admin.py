# File: backend/app/routers/admin.py
"""
Admin-only routes for sensitive operations
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import os

from .. import models
from ..auth import get_current_user, require_roles

router = APIRouter(prefix="/admin", tags=["admin"])


class PasswordValidation(BaseModel):
    password: str


@router.post("/validate-delete-password")
def validate_admin_delete_password(
    payload: PasswordValidation,
    user: models.User = Depends(require_roles("admin"))
):
    """
    Validate password for admin delete operations
    This prevents password from being exposed in frontend code
    """
    # Get password from environment variable or use default
    admin_password = os.getenv("ADMIN_DELETE_PASSWORD", "Kienhp@@123")
    
    return {
        "valid": payload.password == admin_password,
        "message": "Password validated" if payload.password == admin_password else "Invalid password"
    }
