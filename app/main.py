from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.routers import pages, auth, gyms, onboarding, admins, analytics, links, ai_testing

app = FastAPI(title="GymCoach Studio — Dev Console")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten before this is public-facing
    allow_methods=["*"],
    allow_headers=["*"],
)

# No /static mount — every template is self-contained (CSS + JS inline
# in the <head>/<body>), same pattern as the other repos' dashboard.html.

# ── Mounted routers ──────────────────────────────────────────────
# Each one is a self-contained file. To add a new capability later
# (billing, WhatsApp, AI cost tracking) — write app/routers/whatever.py
# and add ONE line here. Nothing above needs to change.
app.include_router(pages.router)
app.include_router(auth.router)
app.include_router(gyms.router)
app.include_router(onboarding.router)
app.include_router(admins.router)
app.include_router(analytics.router)
app.include_router(links.router)
app.include_router(ai_testing.router)


@app.get("/health")
def health():
    return {"status": "ok"}


# ── FUTURE EXTENSIONS — not built, just where they'll plug in ──────
# app.include_router(billing.router)       # Instamojo subscriptions + webhooks
# app.include_router(whatsapp.router)      # member onboarding / reminder sends
# app.include_router(ai_cost_tracking.router)  # token usage, cache hit %, etc.
