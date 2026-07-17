from fastapi import APIRouter, HTTPException, Depends

from bot.database import (
    get_all_volunteers,
    get_volunteer_submissions,
    get_volunteer_by_id,
    get_achievements,
    get_all_events,
    toggle_volunteer_status,
    get_volunteer_reviews,
    get_organizer_rating,
)
from bot.api.routes.auth import get_current_coordinator, get_optional_user

router = APIRouter(tags=["volunteers"])

# Fields never returned over the API, regardless of who's asking.
_ALWAYS_EXCLUDED = {"password_hash"}
# Fields returned only to an authenticated coordinator.
_COORDINATOR_ONLY = {"email", "phone", "telegram_id"}


@router.get("/volunteers")
async def list_volunteers(coordinator=Depends(get_current_coordinator)):
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

    is_coordinator = bool(user) and user.get("role") == "coordinator"
    hidden = _ALWAYS_EXCLUDED if is_coordinator else (_ALWAYS_EXCLUDED | _COORDINATOR_ONLY)
    safe_vol = {k: v for k, v in vol.items() if k not in hidden}

    submissions = await get_volunteer_submissions(volunteer_id)
    achievements = await get_achievements(volunteer_id)
    reviews = await get_volunteer_reviews(volunteer_id)
    org_rating = await get_organizer_rating(volunteer_id)

    events = await get_all_events()
    event_map = {e["id"]: e["title"] for e in events}
    enriched_submissions = []
    for s in submissions:
        enriched_submissions.append({
            **s,
            "event_title": event_map.get(s.get("event_id"), "Мероприятие"),
        })

    return {
        **safe_vol,
        "submissions": enriched_submissions,
        "achievements": achievements,
        "reviews": reviews,
        "organizer_rating": org_rating,
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

    volunteers = await get_all_volunteers()
    vol = None
    for v in volunteers:
        if v["id"] == volunteer_id:
            vol = v
            break

    full_name = vol["full_name"] if vol else ""
    return {"id": volunteer_id, "status": new_status, "full_name": full_name}
