import hashlib
import os
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs

import jwt
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel

from bot.config import settings

router = APIRouter(tags=["auth"])


# ── Password hashing ─────────────


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, dk_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return dk.hex() == dk_hex
    except Exception:
        return False


# ── JWT ───────────────────────────


def create_jwt_token(user_id: int = None, role: str = "coordinator") -> str:
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])


# ── Dependencies ─────────────────


def get_current_user(authorization: str = Header(default="")):
    """Any authenticated user (volunteer or coordinator)."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("user_id"), "role": payload.get("role", "volunteer")}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_coordinator(authorization: str = Header(default="")):
    user = get_current_user(authorization)
    if user["role"] != "coordinator":
        raise HTTPException(status_code=403, detail="Not a coordinator")
    return user


def get_optional_user(authorization: str = Header(default="")):
    """Returns user dict if valid token, None otherwise."""
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return None
    try:
        payload = decode_token(token)
        return {"user_id": payload.get("user_id"), "role": payload.get("role", "volunteer")}
    except Exception:
        return None


# ── Request models ───────────────


class LoginRequest(BaseModel):
    password: str


class VolunteerRegisterRequest(BaseModel):
    full_name: str
    city: str = ""
    email: str
    password: str


class VolunteerLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    token: str
    role: str = "coordinator"
    user_id: int = None
    full_name: str = ""


class WebAppAuthRequest(BaseModel):
    initData: str


# ── Endpoints ────────────────────


@router.post("/auth/login")
async def login_coordinator(request: LoginRequest):
    """Coordinator login with admin password."""
    if request.password != settings.ADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Неверный пароль")
    token = create_jwt_token(user_id=None, role="coordinator")
    return {"token": token, "role": "coordinator", "user_id": None, "full_name": "Координатор"}


@router.post("/auth/register")
async def register_volunteer(request: VolunteerRegisterRequest):
    """Register a new volunteer via web."""
    from bot.database import get_volunteer_by_email, create_volunteer

    if not request.email or not request.password or not request.full_name:
        raise HTTPException(status_code=400, detail="Заполните все обязательные поля")

    if len(request.password) < 4:
        raise HTTPException(status_code=400, detail="Пароль слишком короткий (мин. 4 символа)")

    existing = await get_volunteer_by_email(request.email)
    if existing:
        raise HTTPException(status_code=409, detail="Пользователь с таким email уже существует")

    pw_hash = hash_password(request.password)
    vol_id = await create_volunteer(
        full_name=request.full_name,
        city=request.city,
        email=request.email,
        password_hash=pw_hash,
        role="volunteer",
    )
    token = create_jwt_token(user_id=vol_id, role="volunteer")
    return {"token": token, "role": "volunteer", "user_id": vol_id, "full_name": request.full_name}


@router.post("/auth/login/volunteer")
async def login_volunteer(request: VolunteerLoginRequest):
    """Volunteer login with email + password."""
    from bot.database import get_volunteer_by_email

    volunteer = await get_volunteer_by_email(request.email)
    if not volunteer or not volunteer.get("password_hash"):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    if not verify_password(request.password, volunteer["password_hash"]):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")

    token = create_jwt_token(user_id=volunteer["id"], role=volunteer["role"])
    return {
        "token": token,
        "role": volunteer["role"],
        "user_id": volunteer["id"],
        "full_name": volunteer["full_name"],
    }


@router.get("/auth/me")
async def get_me(user=Depends(get_current_user)):
    """Get current user profile."""
    if user["role"] == "coordinator" and user["user_id"] is None:
        return {"role": "coordinator", "full_name": "Координатор", "user_id": None}

    from bot.database import get_volunteer_by_id
    vol = await get_volunteer_by_id(user["user_id"])
    if not vol:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return {
        "user_id": vol["id"],
        "role": vol["role"],
        "full_name": vol["full_name"],
        "city": vol["city"],
        "email": vol.get("email", ""),
        "points": vol["points"],
        "status": vol["status"],
    }


@router.post("/auth/webapp")
async def webapp_auth(request: WebAppAuthRequest):
    """Authenticate via Telegram WebApp initData."""
    init_data = request.initData
    if not init_data:
        raise HTTPException(status_code=400, detail="No initData")

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

    from bot.database import get_volunteer
    volunteer = await get_volunteer(telegram_id)
    if not volunteer:
        raise HTTPException(status_code=404, detail="User not found")

    role = volunteer["role"]
    token = create_jwt_token(user_id=volunteer["id"], role=role)
    return {
        "token": token,
        "user": {"id": volunteer["id"], "name": volunteer["full_name"], "role": role},
    }
