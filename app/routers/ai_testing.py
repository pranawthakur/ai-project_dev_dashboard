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
    Proxies straight to promptgen-backend's POST /generate/test (separate
    repo), which runs ONLY the deterministic core (split_engine.py /
    programming_rules.py) on a raw profile dict — no member auth, no LLM
    call, no DB write. Lets you sanity-check deterministic engine output
    without going through the member questionnaire flow.

    Requires DEV_TEST_KEY to be set identically on both this service and
    promptgen-backend — see both .env.example files. Left as an explicit
    call (not faked) so it fails loudly instead of returning fabricated
    output if the URL/key isn't right yet.
    """
    target_url = f"{settings.member_app_base_url}/generate/test"
    if not settings.dev_test_key:
        raise HTTPException(
            status_code=503,
            detail="DEV_TEST_KEY is not set on this deployment — set it to match "
                   "promptgen-backend's DEV_TEST_KEY before using AI Engine Test.",
        )
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.post(
                target_url,
                json=body.profile,
                headers={"X-Dev-Test-Key": settings.dev_test_key},
            )
        res.raise_for_status()
        return res.json()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach AI engine at {target_url}: {e}. "
                   f"Confirm the real generation route on the promptgen-backend service.",
        )
