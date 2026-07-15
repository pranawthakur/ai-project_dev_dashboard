# GymCoach Studio — Dev Console

Internal dev/superadmin dashboard. Separate repo, same Supabase project as
`admin-dashboard-backend`.

## Pages
All 8 "pages" live in **one file**: `app/templates/index.html`. Every
server route (`/login`, `/dashboard`, `/gyms`, etc.) serves that same
file; switching between views happens client-side via the URL hash
(`#dashboard`, `#gyms`, `#gyms/<id>`, `#onboarding`, `#admins`, `#links`,
`#ai_testing`) so links, refresh, and back/forward still work.

- `#dashboard` — real-numbers analytics (gyms, members, revenue)
- `#gyms` — list + activate/suspend
- `#gyms/<id>` — single gym detail: members, payments, Excel export
- `#onboarding` — full gym onboarding form (creates gym + first admin together)
- `#admins` — all gym admins, reset password, enable/disable
- `#links` — generate a member access link for any gym, pointing at the
  separate member-facing app (`promptgen-backend` repo)
- `#ai_testing` — send a raw profile straight to the generation engine

## Setup
```
cp .env.example .env      # fill in Supabase creds + JWT secret
pip install -r requirements.txt
psql < schema_patch.sql   # or run in Supabase SQL editor — adds onboarding columns
uvicorn app.main:app --reload
```

Create your first developer login manually (see bottom of `schema_patch.sql`).

## Extending later
Every capability is one file in `app/routers/` + one `include_router()` line
in `app/main.py`. To add:
- **Instamojo billing** → `app/routers/billing.py`
- **WhatsApp automation** → `app/routers/whatsapp.py`
- **AI cost/token analytics** → `app/routers/ai_cost_tracking.py`

None of the existing routers need to change when you add these.

## Not built yet (on purpose)
No fake data anywhere. These need real infra elsewhere first:
- Instamojo subscription billing
- WhatsApp send automation
- AI token/cost/cache-hit tracking
- Login logs, attendance, churn/MAU analytics
