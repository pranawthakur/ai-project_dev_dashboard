from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# ── ONE FILE, ALL PAGES ──────────────────────────────────────────
# index.html contains all 8 views (login + dashboard + gyms + gym
# detail + onboarding + admins + links + ai-testing) as hidden/shown
# <div class="view"> blocks. Routing between them happens client-side
# via the URL hash (#dashboard, #gyms, #gyms/<id>, etc.) — see the
# <script> at the bottom of index.html.
#
# Every server route below just serves the same file so a direct link
# like /gyms or a page refresh still lands correctly; the JS reads
# window.location.hash on load to show the right view.


def render_index(request: Request):
    # NOTE: newer Starlette moved `request` to the first positional arg and
    # dropped the old TemplateResponse("name", {"request": request}) form.
    # Calling the old way on a new Starlette version passes the context dict
    # in as the template *name*, which crashes deep in Jinja2 with
    # "TypeError: unhashable type: 'dict'" — this is that fix.
    return templates.TemplateResponse(request, "index.html")


@router.get("/", response_class=HTMLResponse)
def root(request: Request):
    return render_index(request)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return render_index(request)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return render_index(request)


@router.get("/gyms", response_class=HTMLResponse)
def gyms_page(request: Request):
    return render_index(request)


@router.get("/gyms/{gym_id}", response_class=HTMLResponse)
def gym_detail_page(request: Request, gym_id: str):
    return render_index(request)


@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_page(request: Request):
    return render_index(request)


@router.get("/admins", response_class=HTMLResponse)
def admins_page(request: Request):
    return render_index(request)


@router.get("/links", response_class=HTMLResponse)
def links_page(request: Request):
    return render_index(request)


@router.get("/ai-testing", response_class=HTMLResponse)
def ai_testing_page(request: Request):
    return render_index(request)
