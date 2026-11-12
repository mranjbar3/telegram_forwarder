import io
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from openpyxl import load_workbook

from app.database import get_db
from app.models import SourceChannel, Destination, ActivityLog
from app.api.auth import current_user
from app.services.chat_id import normalize_input

router = APIRouter()


@router.post("/{source_id}/destinations/{dest_id}/delete")
async def delete_destination(
    source_id: int, dest_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    dest = await db.get(Destination, dest_id)
    if dest and dest.source_id == source_id:
        await db.delete(dest)
        db.add(ActivityLog(user=u.username, action="حذف مقصد", detail=dest.chat_id))
        await db.commit()

    return RedirectResponse("/sources", status_code=302)

@router.get("")
async def sources_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    sources = (await db.execute(
        select(SourceChannel).options(selectinload(SourceChannel.destinations))
        .order_by(SourceChannel.id.desc())
    )).scalars().all()
    return templates.TemplateResponse("channels.html", {"request": request, "sources": sources})


@router.post("/create")
async def create_source(
    request: Request,
    chat: str = Form(...),
    title: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")

    try:
        ident = normalize_input(chat)
    except ValueError:
        return RedirectResponse("/sources?err=invalid", status_code=302)

    exists = (await db.execute(
        select(SourceChannel).where(SourceChannel.chat_id == ident)
    )).scalar_one_or_none()
    if exists:
        return RedirectResponse("/sources?err=dup", status_code=302)

    username = ident[1:] if ident.startswith("@") else ""
    db.add(SourceChannel(
        chat_id=ident,
        title=title.strip() or (f"@{username}" if username else ident),
        chat_username=username,
        code=f"SRC-{ident.lstrip('@-')[:20]}",
    ))
    db.add(ActivityLog(user=u.username, action="افزودن کانال", detail=ident))
    await db.commit()
    return RedirectResponse("/sources", status_code=302)


@router.post("/{source_id}/destinations/create")
async def create_destination(
    source_id: int,
    request: Request,
    chat: str = Form(...),
    title: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    try:
        ident = normalize_input(chat)
    except ValueError:
        return RedirectResponse("/sources?err=invalid", status_code=302)

    # جلوگیری از تکرار برای همین منبع
    dup = (await db.execute(
        select(Destination).where(
            Destination.source_id == source_id,
            Destination.chat_id == ident,
        )
    )).scalar_one_or_none()
    if dup:
        return RedirectResponse("/sources?err=dup", status_code=302)

    username = ident[1:] if ident.startswith("@") else ""
    db.add(Destination(
        source_id=source_id,
        chat_id=ident,
        chat_username=username,
        title=title.strip() or (f"@{username}" if username else ident),
    ))
    await db.commit()
    return RedirectResponse("/sources", status_code=302)


@router.post("/import-excel")
async def import_excel(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")

    content = await file.read()
    filename = (file.filename or "").lower()

    rows = []
    if filename.endswith(".csv"):
        import csv
        text = content.decode("utf-8-sig", errors="ignore")
        rows = list(csv.reader(io.StringIO(text)))
    else:
        wb = load_workbook(io.BytesIO(content), data_only=True)
        ws = wb.active
        rows = [list(r) for r in ws.iter_rows(values_only=True)]

    if not rows:
        return RedirectResponse("/sources?err=empty", status_code=302)

    header = [str(c).strip().lower() if c is not None else "" for c in rows[0]]
    idx = {}
    for i, h in enumerate(header):
        if h in ("chat", "chat_id", "channel", "channel_id", "username", "شناسه", "آیدی"):
            idx["chat"] = i
        elif h in ("title", "name", "عنوان", "نام"):
            idx["title"] = i
        elif h in ("category", "دسته"):
            idx["category"] = i

    if "chat" not in idx:
        return RedirectResponse("/sources?err=nocoll", status_code=302)

    added = skipped = 0
    for row in rows[1:]:
        if not row or row[idx["chat"]] is None: continue
        try:
            ident = normalize_input(str(row[idx["chat"]]))
        except ValueError:
            skipped += 1
            continue
        if not ident:
            skipped += 1
            continue
        exists = (await db.execute(
            select(SourceChannel).where(SourceChannel.chat_id == ident)
        )).scalar_one_or_none()
        if exists:
            skipped += 1
            continue
        username = ident[1:] if ident.startswith("@") else ""
        title = ""
        if "title" in idx and row[idx["title"]] is not None:
            title = str(row[idx["title"]]).strip()
        category = "عمومی"
        if "category" in idx and row[idx["category"]] is not None:
            category = str(row[idx["category"]]).strip()
        db.add(SourceChannel(
            chat_id=ident,
            title=title or (f"@{username}" if username else ident),
            chat_username=username,
            category=category,
            code=f"SRC-{ident.lstrip('@-')[:20]}",
        ))
        added += 1

    await db.commit()
    return RedirectResponse(
        f"/sources?imported={added}&skipped={skipped}", status_code=302
    )
