"""
Phase 1 — Developer Dashboard: Manage Plans.

CRUD on membership_plans (build-plan-v2.md §1/§3 Phase 1). This is the
catalog Phase 3's member-facing plan picker reads from, and what Phase 2's
Payment Link generation prices against — so `is_active` is a soft
delete: a plan already referenced by a past payment's `notes.plan_id`
must keep existing, just stop being offered to members. There is no hard
delete endpoint here on purpose.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.db import supabase
from app.core.auth import get_current_developer

router = APIRouter(prefix="/api/plans", tags=["plans"])


@router.get("/{gym_id}")
def list_plans(gym_id: str, _=Depends(get_current_developer)):
    return supabase.table("membership_plans").select("*").eq("gym_id", gym_id).order("duration_months").execute().data


class PlanRequest(BaseModel):
    name: str
    duration_months: int
    price: float


@router.post("/{gym_id}")
def create_plan(gym_id: str, body: PlanRequest, _=Depends(get_current_developer)):
    gym = supabase.table("gyms").select("id").eq("id", gym_id).execute()
    if not gym.data:
        raise HTTPException(status_code=404, detail="Gym not found.")
    if body.duration_months < 1:
        raise HTTPException(status_code=400, detail="Duration must be at least 1 month.")
    if body.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative.")
    row = {
        "gym_id": gym_id,
        "name": body.name.strip(),
        "duration_months": body.duration_months,
        "price": body.price,
        "is_active": True,
    }
    res = supabase.table("membership_plans").insert(row).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create plan.")
    return res.data[0]


@router.put("/plan/{plan_id}")
def update_plan(plan_id: str, body: PlanRequest, _=Depends(get_current_developer)):
    if body.duration_months < 1:
        raise HTTPException(status_code=400, detail="Duration must be at least 1 month.")
    if body.price < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative.")
    supabase.table("membership_plans").update({
        "name": body.name.strip(),
        "duration_months": body.duration_months,
        "price": body.price,
    }).eq("id", plan_id).execute()
    return {"ok": True}


class PlanStatusRequest(BaseModel):
    is_active: bool


@router.put("/plan/{plan_id}/status")
def update_plan_status(plan_id: str, body: PlanStatusRequest, _=Depends(get_current_developer)):
    supabase.table("membership_plans").update({"is_active": body.is_active}).eq("id", plan_id).execute()
    return {"ok": True}
