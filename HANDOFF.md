# HANDOFF — GymCoach Studio Dev Console

Status as of: this build. Read this before touching anything.

## What this repo is
Internal developer/superadmin dashboard. Separate repo from both
`admin-dashboard-backend` (gym admin dashboard) and `promptgen-backend`
(member-facing AI engine). Shares the **same Supabase project** as
`admin-dashboard-backend` — reads/writes the same `gyms` / `admins` /
`members` / `payments` tables, just scoped to `role='developer'`.

It does NOT duplicate the member-facing app. It generates a link that
points at it instead (see "Known gaps" below).

## What's built and working (once env + SQL are set up)
- Developer login (JWT, `role='developer'` only)
- Gym onboarding — one form creates a gym row + first `gym_admin` row
  together, rolls back the gym if admin creation fails
- Gym list + per-gym detail (members, payments, Excel export)
- Gym activate/suspend toggle
- Admin list, password reset, enable/disable
- Access-link generator per gym
- Platform analytics (total gyms, total members, active members, total
  revenue) — computed live from real rows, nothing fabricated
- Retractable sidebar nav, shared theme CSS matching the existing admin
  dashboard (same color vars, same fonts)

## What's stubbed / NOT working yet — do this before demoing
1. **AI Engine Test page will fail.** `app/routers/ai_testing.py` POSTs to
   `{MEMBER_APP_BASE_URL}/generate/test`, which does not exist in
   `promptgen-backend` yet. Either:
   - add a `/generate/test` route there that accepts a raw profile dict
     and returns the generated plan, or
   - tell me the real route name and I'll update the proxy URL.
2. **Access links won't actually work** until `MEMBER_APP_BASE_URL` in
   `.env` points at the real deployed member app AND that app has a
   `/member/login?gym={slug}` route that reads the `gym` query param and
   scopes the questionnaire/login to that gym. Neither exists yet on the
   promptgen-backend side as far as I've seen in the uploaded files —
   confirm before wiring.
3. **No developer account exists yet.** You have to seed one manually
   (see Setup step 4 below) — there's no public signup for `role='developer'`,
   by design.

## Explicitly NOT built (needs other infra first, not faked here)
- Instamojo billing / subscription automation
- WhatsApp send automation (member welcome, payment confirm, expiry reminders)
- AI cost / token / cache-hit tracking
- Login logs, attendance, churn/MAU analytics

Each has a named slot reserved in `app/main.py` (commented at the bottom)
and a suggested file name — `billing.py`, `whatsapp.py`,
`ai_cost_tracking.py`. Build the underlying tracking/integration first,
then the router is a small addition, not a rewrite.

## Setup steps (in order)
1. `cp .env.example .env` — fill in:
   - `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` — same values as
     `admin-dashboard-backend`'s `.env`
   - `JWT_SECRET` — generate a new random one, don't reuse the admin
     dashboard's secret (keeps the two auth systems independent)
   - `MEMBER_APP_BASE_URL` — leave as placeholder until promptgen-backend
     has a confirmed public URL + route (see gap #2 above)
2. `pip install -r requirements.txt`
3. Run `schema_patch.sql` against the Supabase project (SQL editor or
   `psql`) — only adds columns (`owner_name`, `phone`, `city`, `address`,
   `contact_email`, `approx_members` on `gyms`). Doesn't touch or break
   anything `admin-dashboard-backend` depends on.
4. Seed your own developer login — run once, then log in and you can
   reset your own password from `/admins` afterward... actually you can't,
   `/admins` only lists `role='gym_admin'`. For now, reset via SQL directly
   if needed. One-liner to generate the hash:
   ```
   python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('yourpassword'))"
   ```
   Then:
   ```sql
   insert into admins (email, password_hash, role, disabled)
   values ('you@example.com', '<hash from above>', 'developer', false);
   ```
5. `uvicorn app.main:app --reload` — visit `/login`

## Deployment (once ready)
Same pattern as `admin-dashboard-backend`: Render for the FastAPI backend
(pin `runtime.txt` like the other repos — Render's Python auto-detect has
bitten this project before), static assets served from `/static` directly
by FastAPI so no separate Vercel frontend deploy is needed for this repo.

## File map for a fast re-orientation
```
app/main.py              — mounts routers only, read this first
app/core/                — config, db client, JWT auth, password hashing
app/routers/              — one file per API feature, self-contained
app/routers/pages.py        — every route (/, /login, /gyms, etc.) serves
                              the SAME index.html; routing between the 8
                              views happens client-side via URL hash
app/templates/index.html    — THE single file: all 8 pages as <div class="view">
                              blocks, all CSS in one <style>, all JS in one
                              <script>, hash-based router at the bottom
schema_patch.sql            — run this before anything works

To edit one "page": find its `<div class="view" id="view-XXX">` block in
index.html. To restyle everything: one <style> block, top of the file.
```

## Known rough edges (not bugs, just not polished)
- `member_count` per gym in `/api/gyms` does one query per gym — fine at
  current scale (few gyms), will need a proper aggregate/view once gym
  count grows past ~50-100.
- CORS is wide open (`allow_origins=["*"]`) — same as
  `admin-dashboard-backend`, tighten before either is public-facing.
- No rate limiting on `/api/auth/login`.
