from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import supabase
from app.core.security import verify_password
from app.core.auth import create_token

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
def login(body: LoginRequest):
    result = supabase.table("admins").select("*").eq("email", body.email).eq("role", "developer").execute()
    if not result.data:
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    admin = result.data[0]
    if admin.get("disabled"):
        raise HTTPException(status_code=403, detail="This account is disabled.")
    if not verify_password(body.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_token(sub=admin["id"], role="developer")
    return {"access_token": token}
