import random
import string

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.db import supabase
from app.core.security import hash_password
from app.core.auth import get_current_developer
from app.core.config import settings

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


def generate_slug(gym_name: str) -> str:
    base = "".join(c.lower() for c in gym_name if c.isalnum())[:16] or "gym"
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{base}-{suffix}"


class OnboardRequest(BaseModel):
    gym_name: str
    owner_name: str
    phone: str
    contact_email: str
    city: str = ""
    address: str = ""
    approx_members: int = 0
    plan: str = "trial"
    admin_email: str
    admin_password: str


@router.post("")
def onboard_gym(body: OnboardRequest, _=Depends(get_current_developer)):
    existing = supabase.table("admins").select("id").eq("email", body.admin_email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="An admin with this email already exists.")

    slug = generate_slug(body.gym_name)

    gym_row = {
        "name": body.gym_name,
        "slug": slug,
        # gyms.signup_slug is NOT NULL with no default on the live table —
        # gym-dashboard's own /admin/signup route sets this to the same
        # value as slug; mirroring that here so this insert path doesn't
        # 500 with a not-null violation.
        "signup_slug": slug,
        "status": "active",
        "subscription_status": body.plan,
        "owner_name": body.owner_name,
        "phone": body.phone,
        "contact_email": body.contact_email,
        "city": body.city,
        "address": body.address,
        "approx_members": body.approx_members,
    }
    gym_res = supabase.table("gyms").insert(gym_row).execute()
    if not gym_res.data:
        raise HTTPException(status_code=500, detail="Failed to create gym.")
    gym = gym_res.data[0]

    admin_row = {
        "gym_id": gym["id"],
        "email": body.admin_email,
        "password_hash": hash_password(body.admin_password),
        "role": "gym_admin",
        "disabled": False,
    }
    admin_res = supabase.table("admins").insert(admin_row).execute()
    if not admin_res.data:
        # roll back the gym so we don't leave an orphan record behind
        supabase.table("gyms").delete().eq("id", gym["id"]).execute()
        raise HTTPException(status_code=500, detail="Failed to create admin account.")

    access_link = f"{settings.member_app_base_url}/member/login?gym={slug}"

    return {
        "gym_id": gym["id"],
        "slug": slug,
        "access_link": access_link,
    }
