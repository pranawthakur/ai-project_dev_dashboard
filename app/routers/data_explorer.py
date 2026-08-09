from fastapi import APIRouter, Depends, HTTPException

from app.core.db import supabase
from app.core.auth import get_current_developer

router = APIRouter(prefix="/api/data", tags=["data-explorer"])


@router.get("/gyms")
def list_gyms(_=Depends(get_current_developer)):
    """All gyms with a member count and total revenue rollup, for the
    top-level Data Explorer list. Cheap N+1 at current scale — same
    pattern as gyms.py's list_gyms; revisit with a SQL view once gym
    count grows past a few hundred."""
    gyms = supabase.table("gyms").select("*").order("created_at", desc=True).execute().data
    for g in gyms:
        mc = supabase.table("members").select("id", count="exact").eq("gym_id", g["id"]).execute()
        g["member_count"] = mc.count or 0
        pay = supabase.table("payments").select("amount").eq("gym_id", g["id"]).execute().data
        g["total_revenue"] = sum(float(p.get("amount") or 0) for p in pay)
    return gyms


@router.get("/gyms/{gym_id}")
def gym_detail(gym_id: str, _=Depends(get_current_developer)):
    """Full picture for one gym: its members, every payment (member
    fees), and every expense row (this is also where staff salaries
    live if your expenses table tracks them as a category — shown as
    whatever columns actually exist on that row, since this dashboard
    doesn't otherwise touch the expenses table and I don't want to
    assume column names I haven't seen)."""
    gym_res = supabase.table("gyms").select("*").eq("id", gym_id).execute()
    if not gym_res.data:
        raise HTTPException(status_code=404, detail="Gym not found.")
    gym = gym_res.data[0]

    members = supabase.table("members").select("*").eq("gym_id", gym_id).order("name").execute().data

    payments = (
        supabase.table("payments").select("*").eq("gym_id", gym_id)
        .order("created_at", desc=True).execute().data
    )
    member_map = {m["id"]: m.get("name") for m in members}
    for p in payments:
        p["member_name"] = member_map.get(p.get("member_id"), "—")

    try:
        expenses = (
            supabase.table("expenses").select("*").eq("gym_id", gym_id)
            .order("created_at", desc=True).execute().data
        )
    except Exception:
        # Table/columns may not match this shape everywhere — don't let
        # an expenses read failure take down the whole gym detail page.
        expenses = []

    # plan count per member, without pulling every plan's full JSON here
    plan_counts = supabase.table("plans").select("member_id").execute().data
    counts_by_member = {}
    for row in plan_counts:
        mid = row.get("member_id")
        counts_by_member[mid] = counts_by_member.get(mid, 0) + 1
    for m in members:
        m["plan_count"] = counts_by_member.get(m["id"], 0)

    return {"gym": gym, "members": members, "payments": payments, "expenses": expenses}


@router.get("/members/{member_id}")
def member_detail(member_id: str, _=Depends(get_current_developer)):
    """One member's own row (their intake/profile fields live directly
    on this row — whatever the signup form wrote) plus every plan
    they've ever been generated, each with its full week-by-week
    workout breakdown (day_index 0-6 = week 1, 7-13 = week 2 — plans
    are biweekly, see expand_days_to_biweekly in promptgen-backend) and
    the exact intake form snapshot submitted for that specific cycle.
    rendered_html is deliberately left out here (can be large per plan,
    and there can be many plans) — use /plans/{id} for the polished
    member-facing view of one specific plan."""
    member_res = supabase.table("members").select("*").eq("id", member_id).execute()
    if not member_res.data:
        raise HTTPException(status_code=404, detail="Member not found.")
    member = member_res.data[0]

    plans_raw = (
        supabase.table("plans")
        .select("id, cycle_number, status, created_at, valid_until, plan_json")
        .eq("member_id", member_id)
        .order("cycle_number", desc=True)
        .execute()
        .data
    )

    plans = []
    for p in plans_raw:
        plan_json = p.get("plan_json") or {}
        days = (plan_json.get("workout") or {}).get("days") or []
        plans.append({
            "id": p["id"],
            "cycle_number": p.get("cycle_number"),
            "status": p.get("status"),
            "created_at": p.get("created_at"),
            "valid_until": p.get("valid_until"),
            "intake": plan_json.get("_intake") or {},
            "week1_days": days[0:7],
            "week2_days": days[7:14],
        })

    return {"member": member, "plans": plans}


@router.get("/plans/{plan_id}")
def plan_detail(plan_id: str, _=Depends(get_current_developer)):
    """One specific generated plan — the exact intake form snapshot the
    member submitted for this cycle (plan_json._intake, captured at
    generation time — see promptgen-backend's _generate_and_save_plan)
    plus the full rendered HTML, so it can be shown in an iframe
    identical to what the member themselves saw."""
    res = supabase.table("plans").select("*").eq("id", plan_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Plan not found.")
    plan = res.data[0]
    plan_json = plan.get("plan_json") or {}
    return {
        "id": plan["id"],
        "member_id": plan.get("member_id"),
        "cycle_number": plan.get("cycle_number"),
        "status": plan.get("status"),
        "created_at": plan.get("created_at"),
        "valid_until": plan.get("valid_until"),
        "intake": plan_json.get("_intake") or {},
        "rendered_html": plan.get("rendered_html"),
    }
