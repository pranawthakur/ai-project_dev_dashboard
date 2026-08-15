"""
Phase 1 — Developer Dashboard: Razorpay onboarding + notification channel.

Two things live here because they're both captured on the same onboarding
screen (build-plan-v2.md Phase 1), even though they write to two different
tables:
  - gym_payment_config   (Razorpay Key ID / Key Secret / Webhook Secret)
  - gym_messaging_config (which notification channel this gym is on)

Secrets are validated against Razorpay's own API *before* being saved —
catches typos/wrong-account keys at onboarding time instead of at the
first real payment. Only ciphertext ever reaches the DB (see
app/core/crypto_utils.py); this router never returns a decrypted secret
back to the frontend, only whether one is currently set.

Actually creating Razorpay orders / verifying webhooks with these
credentials is Phase 2, in ai-project-gym-dashboard — not here.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.db import supabase
from app.core.auth import get_current_developer
from app.core.config import settings
from app.core.crypto_utils import encrypt_secret

router = APIRouter(tags=["payment-config"])

RAZORPAY_TEST_URL = "https://api.razorpay.com/v1/payments?count=1"


def _verify_razorpay_keys(key_id: str, key_secret: str) -> None:
    """Test-calls Razorpay with the submitted keys. Raises HTTPException
    (400) if they're rejected, so a bad key never gets saved. A trivial
    read-only endpoint (list payments) is used purely as an auth check —
    the response body itself is discarded."""
    try:
        resp = httpx.get(RAZORPAY_TEST_URL, auth=(key_id, key_secret), timeout=10.0)
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach Razorpay to verify keys: {e}")
    if resp.status_code == 401:
        raise HTTPException(status_code=400, detail="Razorpay rejected these keys (401 Unauthorized). Double-check the Key ID and Key Secret.")
    if resp.status_code >= 400:
        raise HTTPException(status_code=400, detail=f"Razorpay returned an unexpected error while verifying keys (status {resp.status_code}).")


# ── Razorpay payment config ─────────────────────────────────────────

@router.get("/api/payment-config/{gym_id}")
def get_payment_config(gym_id: str, _=Depends(get_current_developer)):
    res = supabase.table("gym_payment_config").select("*").eq("gym_id", gym_id).execute()
    row = res.data[0] if res.data else None
    msg_res = supabase.table("gym_messaging_config").select("*").eq("gym_id", gym_id).execute()
    msg_row = msg_res.data[0] if msg_res.data else None
    return {
        "configured": row is not None,
        "razorpay_key_id": row["razorpay_key_id"] if row else None,
        "is_active": row["is_active"] if row else False,
        # Phase 6 — set by ai-project-gym-dashboard's daily key-health cron
        # (app/key_health.py) or immediately on a failed payment-link
        # creation. 'unknown' until the first check runs.
        "key_status": row.get("key_status", "unknown") if row else "unknown",
        "key_status_detail": row.get("key_status_detail") if row else None,
        "key_status_checked_at": row.get("key_status_checked_at") if row else None,
        "webhook_url": f"{settings.gym_dashboard_base_url}/webhooks/razorpay/{gym_id}",
        "notification_channel": msg_row["notification_channel"] if msg_row else "email",
        # Phase 4: approved Twilio Content SIDs for this gym, one per
        # message type — only meaningful when notification_channel is
        # "whatsapp". See ai-project-gym-dashboard/app/messaging.py's
        # docstring for the exact template body each SID must match.
        "twilio_content_sid_welcome": msg_row.get("twilio_content_sid_welcome") if msg_row else None,
        "twilio_content_sid_reminder_t3": msg_row.get("twilio_content_sid_reminder_t3") if msg_row else None,
        "twilio_content_sid_expiry_t0": msg_row.get("twilio_content_sid_expiry_t0") if msg_row else None,
        "twilio_content_sid_final_t15": msg_row.get("twilio_content_sid_final_t15") if msg_row else None,
    }


class PaymentConfigRequest(BaseModel):
    razorpay_key_id: str
    razorpay_key_secret: str
    razorpay_webhook_secret: str


@router.put("/api/payment-config/{gym_id}")
def set_payment_config(gym_id: str, body: PaymentConfigRequest, _=Depends(get_current_developer)):
    gym = supabase.table("gyms").select("id").eq("id", gym_id).execute()
    if not gym.data:
        raise HTTPException(status_code=404, detail="Gym not found.")

    if not body.razorpay_key_id.strip() or not body.razorpay_key_secret.strip():
        raise HTTPException(status_code=400, detail="Key ID and Key Secret are both required.")

    _verify_razorpay_keys(body.razorpay_key_id.strip(), body.razorpay_key_secret.strip())

    try:
        key_secret_encrypted = encrypt_secret(body.razorpay_key_secret.strip())
        webhook_secret_encrypted = (
            encrypt_secret(body.razorpay_webhook_secret.strip()) if body.razorpay_webhook_secret.strip() else None
        )
    except RuntimeError as e:
        # MASTER_ENCRYPTION_KEY not set on this service yet — see
        # DEPLOYMENT_GUIDE.txt Phase 0 step 2/3. Surface this clearly
        # instead of letting it fall through to a generic 500.
        raise HTTPException(status_code=500, detail=str(e))

    row = {
        "gym_id": gym_id,
        "razorpay_key_id": body.razorpay_key_id.strip(),
        "razorpay_key_secret_encrypted": key_secret_encrypted,
        "razorpay_webhook_secret_encrypted": webhook_secret_encrypted,
        "is_active": True,
    }
    # unique(gym_id) on this table — upsert on that constraint so re-saving
    # (key rotation) overwrites rather than erroring on a duplicate row.
    supabase.table("gym_payment_config").upsert(row, on_conflict="gym_id").execute()
    return {"ok": True, "webhook_url": f"{settings.gym_dashboard_base_url}/webhooks/razorpay/{gym_id}"}


class ChannelRequest(BaseModel):
    notification_channel: str  # "email" | "whatsapp"
    # Phase 4 addition — optional, only used when notification_channel is
    # "whatsapp". Blank/omitted fields are left untouched on the existing
    # row (see the upsert below) rather than being wiped, so you can save
    # the channel toggle and the Content SIDs in separate steps if you
    # don't have every template approved yet.
    twilio_content_sid_welcome: str | None = None
    twilio_content_sid_reminder_t3: str | None = None
    twilio_content_sid_expiry_t0: str | None = None
    twilio_content_sid_final_t15: str | None = None


@router.put("/api/messaging-config/{gym_id}")
def set_messaging_channel(gym_id: str, body: ChannelRequest, _=Depends(get_current_developer)):
    if body.notification_channel not in ("email", "whatsapp"):
        raise HTTPException(status_code=400, detail="notification_channel must be 'email' or 'whatsapp'.")
    gym = supabase.table("gyms").select("id").eq("id", gym_id).execute()
    if not gym.data:
        raise HTTPException(status_code=404, detail="Gym not found.")

    row = {"gym_id": gym_id, "notification_channel": body.notification_channel}
    # Only include a Content SID field in the upsert if it was actually
    # submitted (not None) — an upsert with an explicit None would
    # otherwise overwrite/clear an already-approved SID saved earlier.
    for field in (
        "twilio_content_sid_welcome",
        "twilio_content_sid_reminder_t3",
        "twilio_content_sid_expiry_t0",
        "twilio_content_sid_final_t15",
    ):
        value = getattr(body, field)
        if value is not None:
            row[field] = value.strip() or None

    supabase.table("gym_messaging_config").upsert(row, on_conflict="gym_id").execute()
    return {"ok": True}
