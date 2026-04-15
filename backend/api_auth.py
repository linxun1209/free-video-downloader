from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth import (
    create_token,
    get_current_user,
    hash_password,
    validate_email,
    validate_password,
    verify_password,
)
from database import create_user, get_user_by_email, update_user_profile

router = APIRouter(prefix="/api/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    phone: str | None = None
    bio: str | None = None


def _to_profile_text(value: str | None) -> str:
    return value or ""


def _normalize_profile_text(value: str | None) -> str:
    return _to_profile_text(value).strip()


def _build_user_response(user: dict) -> dict:
    is_vip = False
    vip_expire_at = None
    if user.get("is_vip") and user.get("vip_expire_at"):
        try:
            expire = datetime.fromisoformat(user["vip_expire_at"])
            is_vip = expire > datetime.now(timezone.utc)
            vip_expire_at = user["vip_expire_at"]
        except ValueError:
            pass

    return {
        "id": user["id"],
        "email": user["email"],
        "nickname": _to_profile_text(user.get("nickname")),
        "phone": _to_profile_text(user.get("phone")),
        "bio": _to_profile_text(user.get("bio")),
        "is_vip": is_vip,
        "vip_expire_at": vip_expire_at,
    }


@router.post("/register")
async def register(req: RegisterRequest):
    if not validate_email(req.email):
        raise HTTPException(status_code=400, detail="邮箱格式不正确")

    err = validate_password(req.password)
    if err:
        raise HTTPException(status_code=400, detail=err)

    if get_user_by_email(req.email):
        raise HTTPException(status_code=400, detail="该邮箱已注册")

    hashed = hash_password(req.password)
    user = create_user(req.email, hashed)
    token = create_token(user["id"], req.email)

    return {
        "success": True,
        "data": {
            "token": token,
            "user": _build_user_response(user),
        },
    }


@router.post("/login")
async def login(req: LoginRequest):
    user = get_user_by_email(req.email)
    if not user:
        raise HTTPException(status_code=400, detail="邮箱或密码错误")

    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="邮箱或密码错误")

    token = create_token(user["id"], user["email"])
    return {
        "success": True,
        "data": {
            "token": token,
            "user": _build_user_response(user),
        },
    }


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "data": _build_user_response(user),
    }


def _validate_profile_lengths(nickname: str, phone: str, bio: str) -> None:
    if len(nickname) > 30:
        raise HTTPException(status_code=400, detail="昵称长度不能超过 30 个字符")
    if len(phone) > 20:
        raise HTTPException(status_code=400, detail="手机号长度不能超过 20 个字符")
    if len(bio) > 200:
        raise HTTPException(status_code=400, detail="个人简介长度不能超过 200 个字符")


@router.get("/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    return {
        "success": True,
        "data": _build_user_response(user),
    }


@router.put("/profile")
async def put_profile(req: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    nickname = _normalize_profile_text(req.nickname if req.nickname is not None else user.get("nickname"))
    phone = _normalize_profile_text(req.phone if req.phone is not None else user.get("phone"))
    bio = _normalize_profile_text(req.bio if req.bio is not None else user.get("bio"))

    _validate_profile_lengths(nickname, phone, bio)

    updated_user = update_user_profile(user["id"], nickname, phone, bio)
    if not updated_user:
        raise HTTPException(status_code=401, detail="用户不存在")

    return {
        "success": True,
        "data": _build_user_response(updated_user),
    }
