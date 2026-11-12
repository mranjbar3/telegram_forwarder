from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import MessageQueue, MessageStatus
from app.api.auth import current_user

router = APIRouter()

@router.get("")
async def reports_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")

    totals = await db.execute(
        select(MessageQueue.status, func.count()).group_by(MessageQueue.status)
    )
    by_status = dict(totals.all())

    by_dest = await db.execute(
        select(MessageQueue.dest_chat_title, func.count())
        .group_by(MessageQueue.dest_chat_title)
        .order_by(func.count().desc()).limit(10)
    )

    return templates.TemplateResponse("reports.html", {
        "request": request,
        "by_status": by_status,
        "by_dest": list(by_dest.all()),
    })
