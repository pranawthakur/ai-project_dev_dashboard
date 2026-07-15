import io

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openpyxl import Workbook

from app.core.db import supabase
from app.core.auth import get_current_developer

router = APIRouter(prefix="/api/gyms", tags=["gyms"])


@router.get("")
def list_gyms(_=Depends(get_current_developer)):
    gyms = supabase.table("gyms").select("*").order("created_at", desc=True).execute().data
    # member_count per gym — cheap enough at current scale; move to a
    # SQL view/count aggregate once gym count grows past a few hundred.
    for g in gyms:
        count = supabase.table("members").select("id", count="exact").eq("gym_id", g["id"]).execute()
        g["member_count"] = count.count or 0
    return gyms


@router.get("/{gym_id}")
def gym_detail(gym_id: str, _=Depends(get_current_developer)):
    gym_res = supabase.table("gyms").select("*").eq("id", gym_id).execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Gym not found.")
    gym = gym_res.data[0]

    members = supabase.table("members").select("*").eq("gym_id", gym_id).execute().data
    payments = supabase.table("payments").select("*").eq("gym_id", gym_id).order("created_at", desc=True).execute().data

    # attach member name onto each payment for display
    member_map = {m["id"]: m["name"] for m in members}
    for p in payments:
        p["member_name"] = member_map.get(p.get("member_id"), "—")

    return {"gym": gym, "members": members, "payments": payments}


class StatusUpdate(BaseModel):
    status: str  # "active" | "suspended"


@router.put("/{gym_id}/status")
def update_status(gym_id: str, body: StatusUpdate, _=Depends(get_current_developer)):
    if body.status not in ("active", "suspended"):
        raise HTTPException(status_code=400, detail="status must be 'active' or 'suspended'.")
    supabase.table("gyms").update({"status": body.status}).eq("id", gym_id).execute()
    return {"ok": True}


@router.get("/{gym_id}/export")
def export_gym(gym_id: str, _=Depends(get_current_developer)):
    gym_res = supabase.table("gyms").select("*").eq("id", gym_id).execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Gym not found.")
    gym = gym_res.data[0]
    members = supabase.table("members").select("*").eq("gym_id", gym_id).execute().data

    wb = Workbook()
    ws = wb.active
    ws.title = "Members"
    ws.append(["Name", "Phone", "Email", "Login Code", "Status", "Expiry Date"])
    for m in members:
        ws.append([m.get("name"), m.get("phone"), m.get("email"), m.get("login_code"), m.get("status"), m.get("expiry_date")])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    filename = f"{gym['slug']}_members.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
