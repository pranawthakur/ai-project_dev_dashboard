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


settings = Settings()
