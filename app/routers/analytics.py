from datetime import date

from fastapi import APIRouter, Depends

from app.core.db import supabase
from app.core.auth import get_current_developer

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def summary(_=Depends(get_current_developer)):
    gyms = supabase.table("gyms").select("*").order("created_at", desc=True).execute().data
    members = supabase.table("members").select("id, status, expiry_date").execute().data
    payments = supabase.table("payments").select("amount").execute().data

    today = date.today()
    active_members = 0
    for m in members:
        expiry = m.get("expiry_date")
        if m.get("status") == "suspended":
            continue
        if not expiry or date.fromisoformat(expiry) >= today:
            active_members += 1

    total_revenue = sum(float(p.get("amount") or 0) for p in payments)

    return {
        "total_gyms": len(gyms),
        "total_members": len(members),
        "active_members": active_members,
        "total_revenue": total_revenue,
        "recent_gyms": gyms[:5],
    }
