import os
from dataclasses import dataclass


@dataclass
class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "change-me-in-prod")
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 12

    # Base URL of the MEMBER-FACING app (promptgen-backend / login-proj repo).
    # The link generator builds URLs against this. Set to your real deployed
    # member app URL (Vercel/Render) once you wire this up for real.
    member_app_base_url: str = os.getenv("MEMBER_APP_BASE_URL", "https://your-member-app.example.com")

    # Must match DEV_TEST_KEY on the promptgen-backend deployment — see
    # app/routers/ai_testing.py and promptgen-backend/app/main.py's
    # POST /generate/test. Empty -> ai_testing.py's proxy call will get a
    # 401 back from promptgen-backend (fails loudly, as intended).
    dev_test_key: str = os.getenv("DEV_TEST_KEY", "")

    # Gates POST /api/auth/signup (creates role='developer' accounts with
    # full cross-gym access). Empty default matches this project's
    # fail-loudly pattern: unset -> signup always 403s instead of running
    # open. Set a real value before anyone but you can reach this route.
    dev_signup_secret: str = os.getenv("DEV_SIGNUP_SECRET", "")

    # ── Razorpay onboarding (Phase 1) ───────────────────────────────
    # MUST be the exact same value as MASTER_ENCRYPTION_KEY on the
    # gym-admin-dashboard-backend service (see build-plan-v2.md §2.3).
    # This console encrypts a gym's Razorpay secret + webhook secret
    # here, at onboarding time; the gym-dashboard service is what
    # decrypts them later, at webhook/order-creation time (Phase 2).
    # Two different keys = secrets saved here become undecryptable
    # there. Empty -> crypto_utils.py fails loudly instead of storing
    # plaintext. Generate with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    master_encryption_key: str = os.getenv("MASTER_ENCRYPTION_KEY", "")

    # Base URL of the gym-admin-dashboard-backend deployment (Render).
    # Used only to display the per-gym webhook URL
    # (`{gym_dashboard_base_url}/webhooks/razorpay/{gym_id}`) that must be
    # pasted into that gym's own Razorpay dashboard during onboarding
    # (build-plan-v2.md §2.4 — this manual step can't be automated).
    # Default matches render.yaml's service name; override once you know
    # the real deployed URL or a custom domain.
    gym_dashboard_base_url: str = os.getenv(
        "GYM_DASHBOARD_BASE_URL", "https://gym-admin-dashboard-backend.onrender.com"
    )


settings = Settings()
