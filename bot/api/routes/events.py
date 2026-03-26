from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from bot.database import (
    get_all_events,
    create_event,
    update_event_status,
    get_all_volunteers,
)
from bot.api.routes.auth import get_current_coordinator
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
async def list_events():
    events = await get_all_events()
    volunteers = await get_all_volunteers()
    vol_map = {v["id"]: v["full_name"] for v in volunteers}

    result = []
    for ev in events:
        result.append({
            **ev,
            "coordinator_name": vol_map.get(ev["coordinator_id"], "—"),
        })
    return result


@router.post("/events")
async def create_new_event(
    event: EventCreate,
    coordinator=Depends(get_current_coordinator),
):
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
    )
    return {"id": event_id, "qr_code": code}


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
