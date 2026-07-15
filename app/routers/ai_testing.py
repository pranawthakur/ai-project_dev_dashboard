import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_developer
from app.core.config import settings

router = APIRouter(prefix="/api/ai-testing", tags=["ai-testing"])


class TestRequest(BaseModel):
    profile: dict


@router.post("/run")
async def run_test(body: TestRequest, _=Depends(get_current_developer)):
    """
    Proxies straight to the promptgen-backend generation endpoint (separate
    repo) so you can test split_engine.py / progression_context.py output
    without going through the member questionnaire flow.

    TODO: point this at your real generation route once it's confirmed —
    e.g. f"{settings.member_app_base_url}/generate/test". Left as an
    explicit call (not faked) so it fails loudly instead of returning
    fabricated output if the URL/route isn't right yet.
    """
    target_url = f"{settings.member_app_base_url}/generate/test"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(target_url, json=body.profile)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach AI engine at {target_url}: {e}. "
                   f"Confirm the real generation route on the promptgen-backend service.",
        )
