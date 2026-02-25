"""페이지 라우트: HTML 파일 응답."""
import os
from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse

from core import get_current_user

router = APIRouter()
_STATIC = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


def _file(path: str):
    return os.path.join(_STATIC, path)


@router.get("/")
async def root(request: Request):
    p = _file("index.html")
    if os.path.isfile(p):
        return FileResponse(p, media_type="text/html")
    from fastapi import HTTPException
    raise HTTPException(status_code=404, detail="index.html not found")


@router.get("/login")
async def login_page():
    p = _file("login.html")
    if not os.path.isfile(p):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="login.html not found")
    return FileResponse(p, media_type="text/html")


@router.get("/register")
async def register_page():
    p = _file("register.html")
    if not os.path.isfile(p):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="register.html not found")
    return FileResponse(p, media_type="text/html")


@router.get("/dashboard")
async def dashboard_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login", status_code=302)
    p = _file("dashboard.html")
    if not os.path.isfile(p):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="dashboard.html not found")
    return FileResponse(p, media_type="text/html")


@router.get("/admin")
async def admin_page(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login?next=/admin", status_code=302)
    p = _file("admin.html")
    if not os.path.isfile(p):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="admin.html not found")
    return FileResponse(p, media_type="text/html")


@router.get("/survey")
async def survey_page():
    p = _file("survey.html")
    if not os.path.isfile(p):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="survey.html not found")
    return FileResponse(p, media_type="text/html")
