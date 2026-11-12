from fastapi import APIRouter, Depends, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import MessageQueue, MessageStatus
from app.api.auth import current_user
import csv, io
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/export.csv")
async def export_csv(request: Request, status: str = "", db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    q = select(MessageQueue).order_by(MessageQueue.created_at.desc()).limit(10000)
    if status:
        q = q.where(MessageQueue.status == status)
    items = (await db.execute(q)).scalars().all()

    buf = io.StringIO()
    buf.write("\ufeff")  # BOM برای Excel فارسی
    w = csv.writer(buf, quoting=csv.QUOTE_ALL)
    w.writerow(["id","source_chat_id","source_message_id","source_title",
                "dest_chat_id","dest_title","status","retry_count",
                "error","sent_message_id","created_at","sent_at","manual"])
    for m in items:
        w.writerow([
            m.id, m.source_chat_id, m.source_message_id, m.source_chat_title,
            m.dest_chat_id, m.dest_chat_title, m.status, m.retry_count,
            m.error_message or "", m.sent_message_id or "",
            m.created_at.isoformat() if m.created_at else "",
            m.sent_at.isoformat() if m.sent_at else "",
            "yes" if m.manual_source else "no",
        ])
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=queue.csv"})

@router.get("")
async def messages_page(
    request: Request,
    status: str | None = Query(None),
    bookmarked: bool = Query(False),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    from app.main import templates
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    per_page = 50
    q = select(MessageQueue).order_by(MessageQueue.created_at.desc())
    if status:
        q = q.where(MessageQueue.status == status)
    if bookmarked:
        q = q.where(MessageQueue.is_bookmarked.is_(True))
    q = q.offset((page - 1) * per_page).limit(per_page)
    items = (await db.execute(q)).scalars().all()

    return templates.TemplateResponse(
        "messages.html",
        {
            "request": request,
            "active": "records",
            "items": items,
            "status": status,
            "page": page,
            "statuses": [s.value for s in MessageStatus],
            "bookmarked": bookmarked,
        },
    )

@router.post("/{mid}/retry")
async def retry(mid: int, request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    item = await db.get(MessageQueue, mid)
    if item:
        item.status = MessageStatus.PENDING.value
        item.retry_count = 0
        await db.commit()
    return RedirectResponse(request.headers.get("referer", "/queue"), status_code=302)

@router.post("/{mid}/bookmark")
async def bookmark(mid: int, request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    item = await db.get(MessageQueue, mid)
    if item:
        item.is_bookmarked = not item.is_bookmarked
        await db.commit()
    return RedirectResponse(request.headers.get("referer", "/queue"), status_code=302)

@router.get("/{mid}")
async def message_detail(mid: int, request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    item = await db.get(MessageQueue, mid)
    if not item:
        return RedirectResponse("/messages", status_code=302)

    return templates.TemplateResponse("message_detail.html", {
        "request": request, "active": "queue", "item": item,
    })

