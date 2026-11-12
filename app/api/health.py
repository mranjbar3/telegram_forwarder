import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings
from app.api.auth import current_user

router = APIRouter()

@router.get("")
async def health_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")

    checks = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["PostgreSQL"] = ("green", "متصل")
    except Exception as e:
        checks["PostgreSQL"] = ("red", f"خطا: {e}")

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.ping()
        await r.close()
        checks["Redis"] = ("green", "متصل")
    except Exception as e:
        checks["Redis"] = ("red", f"خطا: {e}")

    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getMe")
            ok = r.status_code == 200 and r.json().get("ok")
            checks["Telegram Bot API"] = ("green" if ok else "red",
                                          "متصل" if ok else f"خطا {r.status_code}")
    except Exception as e:
        checks["Telegram Bot API"] = ("red", str(e))

    try:
      async with httpx.AsyncClient(timeout=5) as c:
        r = await c.get(f"{settings.LLAMA_SERVER_URL}/health")
        ok = r.status_code == 200
        checks["LLama Server"] = ("green" if ok else "red",
                                  "متصل" if ok else f"خطا {r.status_code}")
    except Exception as e:
      checks["LLama Server"] = ("red", str(e) or "All connection attempts failed")

    return templates.TemplateResponse("health.html", {"request": request, "checks": checks})
