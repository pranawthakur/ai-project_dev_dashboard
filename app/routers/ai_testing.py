import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
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


class FullTestRequest(BaseModel):
    profile: dict
    slot: str = "1"


@router.post("/run-full")
async def run_full_test(body: FullTestRequest, _=Depends(get_current_developer)):
    """
    Proxies to promptgen-backend's POST /generate/full (see that repo's
    app/main.py + dev_qa_seed.sql) — runs the REAL, full production
    generation pipeline (same as a real member's plan, Trainer Review LLM
    pass included) against one of a handful of fixed internal "Dev QA"
    member accounts, so a developer can see exactly what a member would
    see without needing an actual gym/member login. Returns the rendered
    HTML plan directly (not JSON) so the dev console can show it in an
    iframe for visual quality review. Gated by the same DEV_TEST_KEY
    shared secret as /run above — a developer must already be logged into
    THIS dashboard to reach this route at all (get_current_developer).

    `slot` picks which fixed Dev QA member (DEVQA1/2/3 by default, seeded
    by dev_qa_seed.sql) to run against — lets a couple of people test in
    parallel, or lets one dev switch slots for an unrelated fresh
    baseline vs. reusing a slot to see cycle-over-cycle adaptation.
    """
    target_url = f"{settings.member_app_base_url}/generate/full"
    if not settings.dev_test_key:
        raise HTTPException(
            status_code=503,
            detail="DEV_TEST_KEY is not set on this deployment — set it to match "
                   "promptgen-backend's DEV_TEST_KEY before using AI Engine Test.",
        )
    payload = dict(body.profile)
    payload["_dev_slot"] = body.slot
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            res = await client.post(
                target_url,
                json=payload,
                headers={"X-Dev-Test-Key": settings.dev_test_key},
            )
        if res.status_code >= 400:
            raise HTTPException(status_code=res.status_code, detail=res.text)
        headers = {}
        member_token = res.headers.get("X-Member-Token")
        if member_token:
            headers["X-Member-Token"] = member_token
        return HTMLResponse(content=res.text, headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach AI engine at {target_url}: {e}. "
                   f"Confirm promptgen-backend has been deployed with /generate/full "
                   f"and dev_qa_seed.sql has been run against Supabase.",
        )
