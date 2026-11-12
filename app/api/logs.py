from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import ActivityLog
from app.api.auth import current_user

router = APIRouter()


@router.get("")
async def logs_page(
    request: Request,
    user: str = "",
    db: AsyncSession = Depends(get_db),
):
    from app.main import templates
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    # ─── تجمیع به تفکیک کاربر ───
    agg_rows = (await db.execute(
        select(ActivityLog.user, func.count())
        .group_by(ActivityLog.user)
        .order_by(func.count().desc())
    )).all()
    by_user = [(name or "system", cnt) for name, cnt in agg_rows]
    total_logs = sum(c for _, c in by_user)

    # ─── لاگ‌ها (فیلترشده یا همه) ───
    q = select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(500)
    if user:
        q = q.where(ActivityLog.user == user)
    logs = (await db.execute(q)).scalars().all()

    # ─── آمار اقدامات این کاربر (برای نمایش زیر نمودار) ───
    user_actions = []
    if user:
        ua = (await db.execute(
            select(ActivityLog.action, func.count())
            .where(ActivityLog.user == user)
            .group_by(ActivityLog.action)
            .order_by(func.count().desc())
        )).all()
        user_actions = [(a or "—", c) for a, c in ua]

    return templates.TemplateResponse("logs.html", {
        "request": request, "active": "logs",
        "logs": logs, "by_user": by_user,
        "filter_user": user, "total_logs": total_logs,
        "user_actions": user_actions,
    })
