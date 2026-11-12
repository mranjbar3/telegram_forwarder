from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, ActivityLog
from app.api.auth import current_user, hash_pw, check_pw

router = APIRouter()

@router.get("")
async def profile_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    return templates.TemplateResponse("profile.html", {"request": request, "active": "profile", "me": u})

@router.post("/password")
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")

    if not check_pw(old_password, u.password_hash) or new_password != confirm_password:
        return RedirectResponse("/profile?err=1#password", status_code=302)

    u.password_hash = hash_pw(new_password)
    db.add(ActivityLog(user=u.username, action="تغییر رمز عبور", detail="پروفایل"))
    await db.commit()
    return RedirectResponse("/profile?ok=1#password", status_code=302)
