from fastapi import APIRouter, HTTPException, Depends

from bot.database import (
    get_all_volunteers,
    get_volunteer_submissions,
    get_achievements,
    get_all_events,
    toggle_volunteer_status,
    get_volunteer_reviews,
    get_organizer_rating,
)
from bot.api.routes.auth import get_current_coordinator

router = APIRouter(tags=["volunteers"])


@router.get("/volunteers")
async def list_volunteers():
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
async def get_volunteer_detail(volunteer_id: int):
    volunteers = await get_all_volunteers()
    vol = None
    for v in volunteers:
        if v["id"] == volunteer_id:
            vol = v
            break

    if not vol:
        raise HTTPException(status_code=404, detail="Volunteer not found")

    submissions = await get_volunteer_submissions(volunteer_id)
    achievements = await get_achievements(volunteer_id)
    reviews = await get_volunteer_reviews(volunteer_id)
    org_rating = await get_organizer_rating(volunteer_id)

    # Enrich submissions with event titles
    events = await get_all_events()
    event_map = {e["id"]: e["title"] for e in events}
    enriched_submissions = []
    for s in submissions:
        enriched_submissions.append({
            **s,
            "event_title": event_map.get(s.get("event_id"), "Мероприятие"),
        })

    return {
        **vol,
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

    # Fetch updated volunteer info for the response
    volunteers = await get_all_volunteers()
    vol = None
    for v in volunteers:
        if v["id"] == volunteer_id:
            vol = v
            break

    full_name = vol["full_name"] if vol else ""
    return {"id": volunteer_id, "status": new_status, "full_name": full_name}
