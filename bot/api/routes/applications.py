from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from bot.database import (
    get_event_by_id,
    create_application, get_application, get_event_applications,
    get_volunteer_applications, get_event_application_count,
    create_review, get_event_reviews, get_volunteer_reviews,
    get_event_avg_rating,
    get_volunteer_event_review,
)
from bot.api.routes.auth import get_current_user, get_current_coordinator, get_optional_user

router = APIRouter(tags=["applications"])


class ApplyRequest(BaseModel):
    full_name: str
    email: str
    phone: str = ""


class ReviewRequest(BaseModel):
    rating: int
    comment: str = ""


# ── Applications ─────────────────


@router.post("/events/{event_id}/apply")
async def apply_to_event(event_id: int, req: ApplyRequest, user=Depends(get_current_user)):
    """Volunteer applies to a planned event."""
    event = await get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if event["status"] != "planned":
        raise HTTPException(status_code=400, detail="Заявки принимаются только на предстоящие мероприятия")

    existing = await get_application(event_id, user["user_id"])
    if existing:
        raise HTTPException(status_code=409, detail="Вы уже подали заявку на это мероприятие")

    app_id = await create_application(
        event_id=event_id,
        volunteer_id=user["user_id"],
        full_name=req.full_name,
        email=req.email,
        phone=req.phone,
    )
    return {"id": app_id, "status": "pending"}


@router.get("/events/{event_id}/applications")
async def list_event_applications(event_id: int, user=Depends(get_optional_user)):
    """Get applications for an event. Coordinators see all details, others see count."""
    if user and user["role"] == "coordinator":
        return await get_event_applications(event_id)
    count = await get_event_application_count(event_id)
    return {"count": count}


@router.get("/events/my/applications")
async def my_applications(user=Depends(get_current_user)):
    """Volunteer's own applications."""
    return await get_volunteer_applications(user["user_id"])


@router.get("/events/{event_id}/my-application")
async def my_application_for_event(event_id: int, user=Depends(get_current_user)):
    """Check if current user applied to this event."""
    app = await get_application(event_id, user["user_id"])
    return app or {"applied": False}


@router.get("/events/{event_id}/my-review")
async def my_review_for_event(event_id: int, user=Depends(get_current_user)):
    """Current user's review for this event, if any."""
    r = await get_volunteer_event_review(event_id, user["user_id"])
    return r or {}


# ── Reviews ──────────────────────


@router.post("/events/{event_id}/review")
async def review_event(event_id: int, req: ReviewRequest, user=Depends(get_current_user)):
    """Leave a review for an event you applied to."""
    if req.rating < 1 or req.rating > 5:
        raise HTTPException(status_code=400, detail="Оценка должна быть от 1 до 5")

    event = await get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    if event["status"] != "completed":
        raise HTTPException(status_code=400, detail="Отзыв можно оставить только на завершённое мероприятие")

    app = await get_application(event_id, user["user_id"])
    is_organizer = event.get("created_by") == user["user_id"]
    if not app and not is_organizer:
        raise HTTPException(
            status_code=403,
            detail="Отзыв могут оставить участники с заявкой или организатор мероприятия",
        )

    try:
        review_id = await create_review(
            event_id=event_id,
            volunteer_id=user["user_id"],
            rating=req.rating,
            comment=req.comment,
        )
    except Exception:
        raise HTTPException(status_code=409, detail="Вы уже оставили отзыв на это мероприятие")

    return {"id": review_id}


@router.get("/events/{event_id}/reviews")
async def list_event_reviews(event_id: int):
    """Get reviews for an event (public)."""
    reviews = await get_event_reviews(event_id)
    avg = await get_event_avg_rating(event_id)
    return {"reviews": reviews, **avg}


@router.get("/volunteers/{volunteer_id}/reviews")
async def volunteer_reviews(volunteer_id: int):
    """Reviews written by a volunteer (public)."""
    return await get_volunteer_reviews(volunteer_id)
