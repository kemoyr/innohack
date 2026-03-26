import hashlib
import hmac
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs

import jwt
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

from bot.config import settings

router = APIRouter(tags=["auth"])


class LoginRequest(BaseModel):
    password: str


class TokenResponse(BaseModel):
    token: str


class WebAppAuthRequest(BaseModel):
    initData: str


def create_jwt_token(role: str = "coordinator") -> str:
    payload = {
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def get_current_coordinator(authorization: str = Header(default="")):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        if payload.get("role") != "coordinator":
            raise HTTPException(status_code=403, detail="Not a coordinator")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    if request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Wrong password")
    token = create_jwt_token()
    return TokenResponse(token=token)


@router.post("/auth/webapp")
async def webapp_auth(request: WebAppAuthRequest):
    """Authenticate via Telegram WebApp initData."""
    init_data = request.initData
    if not init_data:
        raise HTTPException(status_code=400, detail="No initData")

    # Parse initData
    try:
        params = parse_qs(init_data)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid initData format")

    user_data = params.get("user", [None])[0]

    if not user_data:
        raise HTTPException(status_code=400, detail="No user in initData")

    try:
        user = json.loads(user_data)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid user data")

    telegram_id = user.get("id")

    if not telegram_id:
        raise HTTPException(status_code=400, detail="No telegram ID")

    # Check if user exists
    from bot.database import get_volunteer
    volunteer = await get_volunteer(telegram_id)

    if not volunteer:
        raise HTTPException(status_code=404, detail="User not found")

    role = volunteer["role"]
    token = create_jwt_token(role=role)

    return {
        "token": token,
        "user": {
            "id": volunteer["id"],
            "name": volunteer["full_name"],
            "role": role,
        },
    }
