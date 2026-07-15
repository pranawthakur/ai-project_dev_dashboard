from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.db import supabase
from app.core.security import hash_password
from app.core.auth import get_current_developer

router = APIRouter(prefix="/api/admins", tags=["admins"])


@router.get("")
def list_admins(_=Depends(get_current_developer)):
    admins = supabase.table("admins").select("*").eq("role", "gym_admin").execute().data
    gyms = {g["id"]: g["name"] for g in supabase.table("gyms").select("id, name").execute().data}
    for a in admins:
        a["gym_name"] = gyms.get(a.get("gym_id"))
        a.pop("password_hash", None)
    return admins


class ResetPasswordRequest(BaseModel):
    new_password: str


@router.post("/{admin_id}/reset-password")
def reset_password(admin_id: str, body: ResetPasswordRequest, _=Depends(get_current_developer)):
    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")
    supabase.table("admins").update({"password_hash": hash_password(body.new_password)}).eq("id", admin_id).execute()
    return {"ok": True}


class StatusUpdate(BaseModel):
    disabled: bool


@router.put("/{admin_id}/status")
def update_status(admin_id: str, body: StatusUpdate, _=Depends(get_current_developer)):
    supabase.table("admins").update({"disabled": body.disabled}).eq("id", admin_id).execute()
    return {"ok": True}
