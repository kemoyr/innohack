from fastapi import APIRouter, HTTPException, Depends

from bot.database import (
    get_all_volunteers,
    get_volunteer_by_id,
    get_volunteer_submissions,
    get_volunteer_points_history,
    get_achievements,
    get_all_events,
    get_events_by_creator,
    toggle_volunteer_status,
    get_volunteer_reviews,
)
from bot.api.routes.auth import get_current_coordinator, get_optional_user

router = APIRouter(tags=["volunteers"])

_SENSITIVE_VOLUNTEER_KEYS = frozenset({"password_hash"})
_PUBLIC_STATUSES = frozenset({"planned", "completed", "cancelled"})


def _strip_sensitive(vol: dict) -> dict:
    if not vol:
        return vol
    return {k: v for k, v in vol.items() if k not in _SENSITIVE_VOLUNTEER_KEYS}


def _public_volunteer_shell(vol: dict) -> dict:
    """Поля профиля без контактов и внутренних данных (для гостей и других волонтёров)."""
    return {
        "id": vol["id"],
        "full_name": vol.get("full_name"),
        "city": vol.get("city") or "",
        "points": vol.get("points") or 0,
        "status": vol.get("status"),
        "role": vol.get("role"),
        "created_at": vol.get("created_at"),
    }


def _build_activity_reports(submissions: list, points_history: list, event_map: dict) -> list:
    """Единая лента: отчёты с формулировкой начисления + прочие баллы (без submission_id)."""
    by_sub: dict = {}
    for row in points_history:
        sid = row.get("submission_id")
        if sid is None:
            continue
        prev = by_sub.get(sid)
        if prev is None or (row.get("id") or 0) > (prev.get("id") or 0):
            by_sub[sid] = row

    items: list = []
    for s in submissions:
        ev_id = s.get("event_id")
        title = event_map.get(ev_id, "Мероприятие")
        ph = by_sub.get(s["id"])
        reason = (ph or {}).get("reason") if ph else None
        reason = (reason or "").strip()
        st = s.get("status") or "pending"
        pts = int(s.get("points_awarded") or 0)
        if not reason:
            if st == "verified" and pts > 0:
                reason = f"Верификация мероприятия №{ev_id}" if ev_id else "Начисление за отчёт"
            elif st == "rejected":
                reason = "Отчёт отклонён, баллы не начислены"
            elif st == "pending":
                reason = "Отчёт на проверке"
            else:
                reason = "Отчёт"
        items.append({
            "kind": "submission",
            "id": s["id"],
            "created_at": s.get("created_at"),
            "event_title": title,
            "status": st,
            "points_awarded": pts,
            "accrual_reason": reason,
        })

    for row in points_history:
        if row.get("submission_id") is not None:
            continue
        amt = int(row.get("amount") or 0)
        reason = (row.get("reason") or "Начисление баллов").strip()
        items.append({
            "kind": "bonus",
            "id": f"bonus-{row['id']}",
            "created_at": row.get("created_at"),
            "event_title": None,
            "status": "bonus",
            "points_awarded": amt,
            "accrual_reason": reason,
        })

    items.sort(key=lambda x: (x.get("created_at") or ""), reverse=True)
    return items


@router.get("/volunteers")
async def list_volunteers(coordinator=Depends(get_current_coordinator)):
    """Полный реестр — только координатор (телефоны, telegram и т.д.)."""
    volunteers = await get_all_volunteers()
    result = []
    for v in volunteers:
        submissions = await get_volunteer_submissions(v["id"])
        result.append({
            "id": v["id"],
            "telegram_id": v["telegram_id"],
            "username": v["username"],
            "full_name": v["full_name"],
            "city": v["city"],
            "phone": v["phone"],
            "role": v["role"],
            "status": v["status"],
            "points": v["points"],
            "submissions_count": len(submissions),
            "created_at": v["created_at"],
        })
    return result


@router.get("/volunteers/{volunteer_id}")
async def get_volunteer_detail(volunteer_id: int, user=Depends(get_optional_user)):
    vol = await get_volunteer_by_id(volunteer_id)
    if not vol:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    achievements = await get_achievements(volunteer_id)
    reviews = await get_volunteer_reviews(volunteer_id)
    created_events = await get_events_by_creator(volunteer_id)

    is_coordinator = bool(user and user.get("role") == "coordinator")
    is_self = bool(user and user.get("user_id") == volunteer_id)

    if is_coordinator or is_self:
        submissions = await get_volunteer_submissions(volunteer_id)
        points_history = await get_volunteer_points_history(volunteer_id)
        events = await get_all_events()
        event_map = {e["id"]: e["title"] for e in events}
        activity_reports = _build_activity_reports(submissions, points_history, event_map)
        return {
            **_strip_sensitive(vol),
            "activity_reports": activity_reports,
            "created_events": created_events,
            "achievements": achievements,
            "reviews": reviews,
            "profile_scope": "full",
        }

    public_events = [e for e in created_events if e.get("status") in _PUBLIC_STATUSES]
    return {
        **_public_volunteer_shell(vol),
        "activity_reports": [],
        "created_events": public_events,
        "achievements": achievements,
        "reviews": reviews,
        "profile_scope": "public",
    }


@router.patch("/volunteers/{volunteer_id}/status")
async def toggle_status(
    volunteer_id: int,
    coordinator=Depends(get_current_coordinator),
):
    """Toggle volunteer status between active and inactive."""
    new_status = await toggle_volunteer_status(volunteer_id)
    if new_status is None:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    vol = await get_volunteer_by_id(volunteer_id)
    full_name = vol["full_name"] if vol else ""
    return {"id": volunteer_id, "status": new_status, "full_name": full_name}
