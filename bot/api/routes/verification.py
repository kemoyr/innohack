"""Event verification and moderation routes."""
import json
import os
import tempfile

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

from bot.api.routes.auth import get_current_user, get_current_coordinator
from bot.config import settings
from bot.database import (
    get_event_by_id, create_event_verification, get_event_verification,
    get_pending_verifications, get_all_verifications,
    update_verification_decision, moderate_event,
    get_pending_events, get_events_by_creator,
)
from bot.utils.ai_moderation import run_moderation

router = APIRouter(tags=["verification"])


@router.post("/events/{event_id}/verify")
async def upload_verification(
    event_id: int,
    location_lat: float = Form(0.0),
    location_lon: float = Form(0.0),
    photos: list[UploadFile] = File(default=[]),
    user=Depends(get_current_user),
):
    """Volunteer uploads verification data (photos + geolocation) for their event."""
    event = await get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    if event.get("created_by") != user["user_id"] and user["role"] != "coordinator":
        raise HTTPException(status_code=403, detail="Нет доступа")

    if event["status"] not in ("pending",):
        raise HTTPException(status_code=400, detail="Мероприятие уже проверено")

    temp_paths = []
    try:
        for photo in photos:
            suffix = os.path.splitext(photo.filename or "img.jpg")[1] or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                content = await photo.read()
                tmp.write(content)
                temp_paths.append(tmp.name)

        result = run_moderation(
            photo_paths=temp_paths,
            lat=location_lat if location_lat != 0 else None,
            lon=location_lon if location_lon != 0 else None,
            title=event["title"],
            description=event.get("description", ""),
            demo_mode=settings.DEMO_MODE,
        )
    finally:
        for p in temp_paths:
            try:
                os.unlink(p)
            except OSError:
                pass

    ver_id = await create_event_verification(
        event_id=event_id,
        volunteer_id=user["user_id"],
        photo_paths=json.dumps([p.filename for p in photos]),
        lat=location_lat if location_lat != 0 else None,
        lon=location_lon if location_lon != 0 else None,
        ai_score=result["score"],
        ai_approved=1 if result["approved"] else 0,
        ai_reasons=json.dumps(result["reasons"], ensure_ascii=False),
    )

    if result["approved"]:
        await moderate_event(event_id, "planned", "Автоматически одобрено ИИ")

    return {
        "verification_id": ver_id,
        "ai_approved": result["approved"],
        "ai_score": result["score"],
        "ai_reasons": result["reasons"],
        "ai_details": result["details"],
        "event_status": "planned" if result["approved"] else "pending",
    }


@router.get("/events/{event_id}/verification")
async def get_verification_status(event_id: int, user=Depends(get_current_user)):
    """Get verification status for an event."""
    ver = await get_event_verification(event_id)
    if not ver:
        return {"verified": False, "verification": None}

    return {
        "verified": True,
        "verification": {
            **ver,
            "ai_reasons": json.loads(ver.get("ai_reasons", "[]")),
            "photo_paths": json.loads(ver.get("photo_paths", "[]")),
        },
    }


@router.get("/events/my/list")
async def my_events(user=Depends(get_current_user)):
    """Events created by the current volunteer."""
    events = await get_events_by_creator(user["user_id"])
    result = []
    for ev in events:
        ver = await get_event_verification(ev["id"])
        result.append({
            **ev,
            "has_verification": ver is not None,
            "ai_approved": ver["ai_approved"] if ver else None,
        })
    return result

class ModerationAction(BaseModel):
    action: str  # "approve" or "reject"
    comment: str = ""


@router.get("/moderation/queue")
async def moderation_queue(coordinator=Depends(get_current_coordinator)):
    """Get events needing coordinator review (AI rejected)."""
    items = await get_pending_verifications()
    result = []
    for item in items:
        result.append({
            **item,
            "ai_reasons": json.loads(item.get("ai_reasons", "[]")),
            "photo_paths": json.loads(item.get("photo_paths", "[]")),
        })
    return result


@router.get("/moderation/history")
async def moderation_history(coordinator=Depends(get_current_coordinator)):
    """Full moderation history."""
    items = await get_all_verifications()
    result = []
    for item in items:
        result.append({
            **item,
            "ai_reasons": json.loads(item.get("ai_reasons", "[]")),
            "photo_paths": json.loads(item.get("photo_paths", "[]")),
        })
    return result


@router.post("/moderation/{event_id}/decide")
async def coordinator_decide(
    event_id: int,
    data: ModerationAction,
    coordinator=Depends(get_current_coordinator),
):
    """Coordinator approves or rejects a pending event."""
    event = await get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Мероприятие не найдено")

    if event["status"] != "pending":
        raise HTTPException(status_code=400, detail="Мероприятие не ожидает проверки")

    ver = await get_event_verification(event_id)

    if data.action == "approve":
        await moderate_event(event_id, "planned", data.comment or "Одобрено координатором")
        if ver:
            await update_verification_decision(ver["id"], "approved", data.comment)
        return {"ok": True, "status": "planned"}
    elif data.action == "reject":
        await moderate_event(event_id, "rejected", data.comment or "Отклонено координатором")
        if ver:
            await update_verification_decision(ver["id"], "rejected", data.comment)
        return {"ok": True, "status": "rejected"}
    else:
        raise HTTPException(status_code=400, detail="Неизвестное действие")
