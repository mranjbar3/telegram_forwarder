from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models import User
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Setting
from app.api import (
    auth, dashboard, messages, sources, rules, llm_prompts,
    users, reports, publish, logs, health, settings as settings_api, categories, profile,
    notifications, cleaning,
)
from app.i18n import get_lang, is_rtl, t, LANGS
from app.constants import COUNTRIES, country_name, country_flag
from jinja2 import pass_context

class I18nMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        lang = get_lang(request)
        request.state.lang = lang
        request.state.dir = "rtl" if is_rtl(lang) else "ltr"

        # عنوان سایت بر اساس زبان + تنظیمات
        request.state.app_title = "پنل فورواردر"
        try:
            async with AsyncSessionLocal() as db:
                rows = (await db.execute(
                    select(Setting).where(Setting.key.in_(
                        ["app_title_fa", "app_title_en", "app_title_ar"]
                    ))
                )).scalars().all()
                m = {r.key: r.value for r in rows if r.value and r.value.strip()}
                key = {"fa": "app_title_fa", "en": "app_title_en", "ar": "app_title_ar"}[lang]
                if m.get(key):
                    request.state.app_title = m[key]
                elif m.get("app_title_fa"):
                    request.state.app_title = m["app_title_fa"]
        except Exception:
            pass
        return await call_next(request)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ایجاد ادمین پیش‌فرض اگر نبود
    async with AsyncSessionLocal() as db:
        exists = (await db.execute(select(User).where(User.username == "admin"))).scalar_one_or_none()
        if not exists:
            from app.api.auth import hash_pw
            db.add(User(username="admin", full_name="مدیر اصلی",
                        password_hash=hash_pw(settings.ADMIN_PASSWORD), role="admin"))
            await db.commit()
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)
app.add_middleware(I18nMiddleware)
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(dashboard.router, tags=["dashboard"])
app.include_router(messages.router, prefix="/messages", tags=["messages"])
app.include_router(sources.router, prefix="/sources", tags=["sources"])
app.include_router(rules.router, prefix="/rules", tags=["rules"])
app.include_router(llm_prompts.router, prefix="/prompts", tags=["prompts"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(publish.router, prefix="/publish", tags=["publish"])
app.include_router(logs.router, prefix="/logs", tags=["logs"])
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(settings_api.router, prefix="/settings", tags=["settings"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
app.include_router(cleaning.router, prefix="/cleaning", tags=["cleaning"])

class AppTitleMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.app_title = "Telegram Mirror Pro"  # پیش‌فرض
        try:
            async with AsyncSessionLocal() as db:
                s = (await db.execute(
                    select(Setting).where(Setting.key == "app_title")
                )).scalar_one_or_none()
                if s and s.value.strip():
                    request.state.app_title = s.value.strip()
        except Exception:
            pass
        return await call_next(request)

app.add_middleware(AppTitleMiddleware)
# Jinja globals
templates.env.globals["t"] = lambda key: t(key, request_state_lang(templates, key))

def _t_from_ctx(ctx, key):
    lang = ctx.get("request").state.lang if ctx.get("request") else "fa"
    return t(key, lang)

@pass_context
def _t(ctx, key):
    req = ctx.get("request")
    lang = req.state.lang if req and hasattr(req.state, "lang") else "fa"
    return t(key, lang)

templates.env.globals["t"] = _t
templates.env.globals["lang_name"] = country_name
templates.env.globals["lang_flag"] = country_flag
templates.env.globals["COUNTRIES"] = COUNTRIES

@app.get("/")
async def root():
    return RedirectResponse("/dashboard")

@app.get("/healthz")
def healthz():
    return {"ok": True}

@app.get("/lang/{code}")
async def set_lang(code: str, request: Request):
    if code in LANGS:
        request.session["lang"] = code
    return RedirectResponse(request.headers.get("referer", "/dashboard"), status_code=302)


