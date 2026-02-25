"""인증·회원 API 및 폼 로그인."""
import os
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from core import get_current_user, is_admin, USERS_DEMO, db_error_message

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/api/register")
async def api_register(body: RegisterRequest):
    try:
        from user_storage import register
        out = register(body.email.strip(), body.password)
        return {"ok": True, "email": out["email"], "created_at": out["created_at"]}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=503, detail=db_error_message(e))


@router.post("/api/login")
async def api_login(request: Request, body: LoginRequest):
    email = body.email.strip().lower()
    pw = USERS_DEMO.get(email)
    if pw is None:
        try:
            from user_storage import verify_password
            if not verify_password(email, body.password):
                raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        except ImportError:
            raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
        except Exception as e:
            raise HTTPException(status_code=503, detail=db_error_message(e))
    elif pw != body.password:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    request.session["user"] = {"email": email, "name": email.split("@")[0]}
    return {"ok": True, "email": email}


@router.get("/api/logout")
async def api_logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)


@router.get("/api/me")
async def api_me(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
    return {**user, "is_admin": is_admin(user)}


@router.post("/login")
async def login_submit(
    request: Request,
    email: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    next_url: Optional[str] = Form(None, alias="next"),
):
    email = (email or "").strip().lower()
    pw = USERS_DEMO.get(email)
    if pw is None:
        try:
            from user_storage import verify_password
            if not email or not verify_password(email, password or ""):
                return RedirectResponse(url="/login?error=1", status_code=302)
        except ImportError:
            return RedirectResponse(url="/login?error=1", status_code=302)
    elif not email or pw != (password or ""):
        return RedirectResponse(url="/login?error=1", status_code=302)
    request.session["user"] = {"email": email, "name": email.split("@")[0]}
    dest = (next_url or "").strip() or "/dashboard"
    if dest.startswith("/admin") and email == "admin@test.com":
        return RedirectResponse(url="/admin", status_code=302)
    if dest.startswith("/") and not dest.startswith("//"):
        return RedirectResponse(url=dest, status_code=302)
    return RedirectResponse(url="/dashboard", status_code=302)
