from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.db import supabase
from app.core.security import verify_password, hash_password
from app.core.auth import create_token
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str
    signup_secret: str


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


# Gated by DEV_SIGNUP_SECRET (see app/core/config.py) — unset means this
# always 403s rather than running open.
@router.post("/signup")
def signup(body: SignupRequest):
    if not settings.dev_signup_secret or body.signup_secret != settings.dev_signup_secret:
        raise HTTPException(status_code=403, detail="Invalid signup secret.")

    existing = supabase.table("admins").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    password_hash = hash_password(body.password)
    result = (
        supabase.table("admins")
        .insert({
            "email": body.email,
            "password_hash": password_hash,
            "role": "developer",
            "disabled": False,
        })
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=500, detail="Could not create account.")

    admin = result.data[0]
    token = create_token(sub=admin["id"], role="developer")
    return {"access_token": token}

