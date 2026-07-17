from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from bot.database import (
    get_all_events, get_public_events, get_pending_events,
    create_event, update_event_status, get_all_volunteers,
    get_event_by_id, get_event_application_count, get_event_avg_rating,
)
from bot.api.routes.auth import get_current_coordinator, get_current_user, get_optional_user
from bot.utils.qr import generate_event_code

router = APIRouter(tags=["events"])


class EventCreate(BaseModel):
    title: str
    description: str = ""
    location_name: str = ""
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    scheduled_date: str = ""


class EventUpdate(BaseModel):
    status: Optional[str] = None
    attendance_count: Optional[int] = None


@router.get("/events")
async def list_events(user=Depends(get_optional_user)):
    """List events. Public users see only published events. Coordinators see all."""
    if user and user["role"] == "coordinator":
        events = await get_all_events()
    else:
        events = await get_public_events()

    volunteers = await get_all_volunteers()
    vol_map = {v["id"]: v["full_name"] for v in volunteers}

    result = []
    for ev in events:
        app_count = await get_event_application_count(ev["id"])
        avg = await get_event_avg_rating(ev["id"])
        result.append({
            **ev,
            "coordinator_name": vol_map.get(ev.get("coordinator_id"), "—"),
            "creator_name": vol_map.get(ev.get("created_by"), "—"),
            "application_count": app_count,
            "avg_rating": avg["avg_rating"],
            "review_count": avg["count"],
        })
    return result


@router.get("/events/pending")
async def list_pending_events(coordinator=Depends(get_current_coordinator)):
    """Coordinator: list all pending events."""
    return await get_pending_events()


@router.get("/events/{event_id}")
async def get_event(event_id: int):
    """Get single event detail (public)."""
    event = await get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")
    return event


@router.post("/events")
async def create_new_event(
    event: EventCreate,
    user=Depends(get_current_user),
):
    """Create event. Coordinators create planned events directly. Volunteers create pending ones."""
    if user["role"] == "coordinator":
        code = generate_event_code()
        event_id = await create_event(
            title=event.title,
            description=event.description,
            location_name=event.location_name,
            lat=event.location_lat,
            lon=event.location_lon,
            scheduled_date=event.scheduled_date,
            qr_code=code,
            coordinator_id=None,
            status="planned",
        )
        return {"id": event_id, "qr_code": code, "status": "planned"}
    else:
        event_id = await create_event(
            title=event.title,
            description=event.description,
            location_name=event.location_name,
            lat=event.location_lat,
            lon=event.location_lon,
            scheduled_date=event.scheduled_date,
            created_by=user["user_id"],
            status="pending",
        )
        return {"id": event_id, "status": "pending"}


@router.patch("/events/{event_id}")
async def update_event(
    event_id: int,
    data: EventUpdate,
    coordinator=Depends(get_current_coordinator),
):
    status = data.status or "completed"
    attendance = data.attendance_count or 0
    await update_event_status(event_id, status, attendance)
    return {"ok": True}
