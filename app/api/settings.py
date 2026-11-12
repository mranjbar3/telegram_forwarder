from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Setting, ActivityLog
from app.api.auth import current_user

router = APIRouter()

KNOWN_KEYS = [
    ("app_title_fa", "عنوان (فارسی)",     "پنل فورواردر"),
    ("app_title_en", "Title (English)",    "Forwarder Panel"),
    ("app_title_ar", "العنوان (العربية)",  "لوحة الإدارة"),
    ("rate_limit",   "حداکثر پیام بر ثانیه", "30"),
    ("min_delay",    "حداقل تأخیر (ثانیه)",  "0.05"),
    ("retry_max",    "حداکثر تلاش مجدد",     "5"),
    ("backup_interval", "فاصله بکاپ (ساعت)", "24"),
]

@router.get("")
async def settings_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    rows = (await db.execute(select(Setting))).scalars().all()
    values = {r.key: r.value for r in rows}
    return templates.TemplateResponse("settings.html", {
        "request": request, "keys": KNOWN_KEYS, "values": values,
    })

@router.post("/save")
async def save_settings(request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    form = await request.form()
    for key, _, default in KNOWN_KEYS:
        val = str(form.get(key, default))
        existing = await db.get(Setting, key)
        if existing:
            existing.value = val
        else:
            db.add(Setting(key=key, value=val))
    db.add(ActivityLog(user=u.username, action="ویرایش تنظیمات", detail="عمومی"))
    await db.commit()
    return RedirectResponse("/settings", status_code=302)
