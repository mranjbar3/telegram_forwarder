import logging
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Notification, NotificationRead, ActivityLog
from app.api.auth import current_user

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def notifications_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")
    items = (await db.execute(
        select(Notification).order_by(Notification.created_at.desc()).limit(100)
    )).scalars().all()
    return templates.TemplateResponse("notifications.html", {
        "request": request, "active": "notifications", "items": items, "me": u,
    })


@router.get("/my")
async def my_notifications(request: Request, db: AsyncSession = Depends(get_db)):
    """JSON برای dropdown. همیشه پاسخ معتبر برمی‌گرداند."""
    try:
        u = await current_user(request, db)
        if not u:
            return JSONResponse({"items": [], "unread": 0, "error": "not_logged_in"})

        rows = (await db.execute(
            select(Notification)
            .where(or_(Notification.target_role == "", Notification.target_role == u.role))
            .order_by(Notification.created_at.desc())
            .limit(20)
        )).scalars().all()

        read_ids = set((await db.execute(
            select(NotificationRead.notification_id).where(NotificationRead.user_id == u.id)
        )).scalars().all())

        unread = sum(1 for r in rows if r.id not in read_ids)

        return JSONResponse({
            "unread": unread,
            "items": [
                {
                    "id": r.id,
                    "title": r.title,
                    "body": r.body[:200],
                    "level": r.level,
                    "read": r.id in read_ids,
                    "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                }
                for r in rows
            ],
        })
    except Exception as e:
        logger.exception("my_notifications failed")
        return JSONResponse({"items": [], "unread": 0, "error": str(e)}, status_code=200)


@router.post("/create")
async def create_notification(
    request: Request,
    title: str = Form(...), body: str = Form(...),
    level: str = Form("info"), target_role: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u or u.role != "admin":
        return RedirectResponse("/auth/login")
    db.add(Notification(
        title=title.strip(), body=body.strip(),
        level=level if level in ("info","warning","error","success") else "info",
        target_role=target_role.strip(), created_by=u.username,
    ))
    db.add(ActivityLog(user=u.username, action="ارسال اعلان", detail=title[:60]))
    await db.commit()
    return RedirectResponse("/notifications", status_code=302)


@router.post("/{nid}/delete")
async def delete_notification(nid: int, request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u or u.role != "admin":
        return RedirectResponse("/auth/login")
    n = await db.get(Notification, nid)
    if n:
        await db.delete(n)
        await db.commit()
    return RedirectResponse("/notifications", status_code=302)


@router.post("/{nid}/read")
async def mark_read(nid: int, request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u:
        return JSONResponse({"ok": False})
    existing = (await db.execute(
        select(NotificationRead).where(
            NotificationRead.notification_id == nid,
            NotificationRead.user_id == u.id,
        )
    )).scalar_one_or_none()
    if not existing:
        db.add(NotificationRead(notification_id=nid, user_id=u.id))
        await db.commit()
    return JSONResponse({"ok": True})
