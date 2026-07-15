from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# NOTE: pages are plain server-rendered HTML. Auth is enforced client-side
# (nav.js redirects to /login if no token) AND server-side on every /api/*
# call via get_current_developer. A page loading without a valid token just
# shows empty tables until redirected — no sensitive data ever renders
# server-side into these templates.


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/gyms", response_class=HTMLResponse)
def gyms_page(request: Request):
    return templates.TemplateResponse("gyms.html", {"request": request})


@router.get("/gyms/{gym_id}", response_class=HTMLResponse)
def gym_detail_page(request: Request, gym_id: str):
    return templates.TemplateResponse("gym_detail.html", {"request": request, "gym_id": gym_id})


@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(request: Request):
    return templates.TemplateResponse("onboarding.html", {"request": request})


@router.get("/admins", response_class=HTMLResponse)
def admins_page(request: Request):
    return templates.TemplateResponse("admins.html", {"request": request})


@router.get("/links", response_class=HTMLResponse)
def links_page(request: Request):
    return templates.TemplateResponse("links.html", {"request": request})


@router.get("/ai-testing", response_class=HTMLResponse)
def ai_testing_page(request: Request):
    return templates.TemplateResponse("ai_testing.html", {"request": request})
