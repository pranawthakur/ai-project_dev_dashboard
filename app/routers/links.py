from fastapi import APIRouter, Depends, HTTPException

from app.core.db import supabase
from app.core.auth import get_current_developer
from app.core.config import settings

router = APIRouter(prefix="/api/links", tags=["links"])


@router.get("/{gym_id}")
def get_link(gym_id: str, _=Depends(get_current_developer)):
    gym_res = supabase.table("gyms").select("slug, name").eq("id", gym_id).execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Gym not found.")
    slug = gym_res.data[0]["slug"]

    # Points at the MEMBER-FACING app (separate repo: promptgen-backend /
    # login-proj), not this dev console. Update MEMBER_APP_BASE_URL in env
    # once that app has its real deployed URL / routing wired in.
    access_link = f"{settings.member_app_base_url}/member/login?gym={slug}"
    return {"gym_id": gym_id, "slug": slug, "access_link": access_link}
