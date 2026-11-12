from datetime import datetime, timezone

import bcrypt  # ← ایمپورت مستقیم
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, ActivityLog

router = APIRouter()


def hash_pw(p: str) -> str:
    # bcrypt محدودیت 72 بایت دارد؛ رمزهای طولانی‌تر را به‌صورت امن کوتاه می‌کنیم
    pw_bytes = p.encode("utf-8")[:72]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def check_pw(p: str, h: str) -> bool:
    pw_bytes = p.encode("utf-8")[:72]
    try:
        return bcrypt.checkpw(pw_bytes, h.encode("utf-8"))
    except ValueError:
        return False


def require_login(request: Request):
    if not request.session.get("user_id") and not request.session.get("logged_in"):
        raise HTTPException(status_code=302, headers={"Location": "/auth/login"})


async def current_user(request: Request, db: AsyncSession) -> User | None:
    uid = request.session.get("user_id")
    if not uid:
        return None
    return await db.get(User, uid)


@router.get("/login")
async def login_page(request: Request):
    from app.main import templates
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    from app.main import templates

    user = (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()

    if not user or not user.is_active or not check_pw(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "نام کاربری یا رمز اشتباه است"},
            status_code=401,
        )

    user.last_login = datetime.now(timezone.utc)
    db.add(ActivityLog(user=user.username, action="ورود موفق", detail="پنل مدیریت"))
    await db.commit()

    request.session["user_id"] = user.id
    request.session["logged_in"] = True

    return RedirectResponse("/dashboard", status_code=302)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/auth/login", status_code=302)
