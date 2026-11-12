from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import MessageQueue, MessageStatus, SourceChannel
from app.api.auth import current_user
from collections import defaultdict

router = APIRouter()

@router.get("/dashboard")
async def dashboard_page(request: Request, country: str = "", db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    # پایه: کل کانال‌ها
    total = await db.scalar(select(func.count()).select_from(SourceChannel)) or 0
    active = await db.scalar(select(func.count()).select_from(SourceChannel).where(SourceChannel.is_active)) or 0

    # شمارش پیام‌ها به تفکیک وضعیت
    counts = {s.value: await db.scalar(
        select(func.count()).select_from(MessageQueue).where(MessageQueue.status == s.value)
    ) for s in MessageStatus}
    sent_today = await db.scalar(
        select(func.count()).select_from(MessageQueue)
        .where(MessageQueue.status == "sent",
               MessageQueue.sent_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0))
    ) or 0

    # کانال‌ها به تفکیک کشور
    by_country_rows = (await db.execute(
        select(SourceChannel.country, func.count())
        .group_by(SourceChannel.country)
    )).all()
    by_country = {c or "ir": n for c, n in by_country_rows}

    # فیلتر انتخابی
    q = select(SourceChannel)
    if country:
        q = q.where(SourceChannel.country == country)
    sources = (await db.execute(q)).scalars().all()

    # پیام‌ها به تفکیک source_chat_id (برای پرتولیدترین کانال‌ها)
    msg_count_rows = (await db.execute(
        select(MessageQueue.source_chat_id, func.count())
        .group_by(MessageQueue.source_chat_id)
        .order_by(func.count().desc())
        .limit(200)
    )).all()
    msg_count = {cid: n for cid, n in msg_count_rows}

    # پرتولیدترین کانال‌های همان کشور
    top_channels = []
    for s in sources:
        cnt = msg_count.get(s.chat_id, 0)
        top_channels.append({"id": s.id, "title": s.title, "count": cnt, "country": s.country})
    top_channels.sort(key=lambda x: x["count"], reverse=True)
    top_channels = top_channels[:15]

    return templates.TemplateResponse("dashboard.html", {
        "request": request, "active": "dashboard",
        "total_channels": total, "active_channels": active,
        "sent": counts.get("sent", 0), "pending": counts.get("pending", 0),
        "failed": counts.get("failed", 0), "sent_today": sent_today,
        "by_country": by_country, "selected_country": country,
        "top_channels": top_channels,
    })
