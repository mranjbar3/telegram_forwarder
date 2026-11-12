from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import (
    SourceChannel, Destination, MessageQueue, MessageStatus, ActivityLog,
    FilterRule, LLMPrompt,
)
from app.api.auth import current_user
from app.services.filter import FilterService

router = APIRouter()


@router.get("")
async def publish_page(request: Request, country: str = "", db: AsyncSession = Depends(get_db)):
    from app.main import templates
    from app.constants import COUNTRIES
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    q = select(SourceChannel).options(selectinload(SourceChannel.destinations)).where(SourceChannel.is_active)
    if country:
        q = q.where(SourceChannel.country == country)
    sources = (await db.execute(q)).scalars().all()

    return templates.TemplateResponse("publish.html", {
        "request": request, "active": "publish",
        "sources": sources, "selected_country": country,
    })


@router.post("/send")
async def publish_send(
    request: Request,
    text: str = Form(...),
    dest_ids: list[str] = Form(default=[]),
    is_ad: str = Form("0"),
    project_name: str = Form(""),
    apply_filters: str = Form("0"),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")

    dest_ids = [d.strip() for d in dest_ids if d and d.strip()]
    if not dest_ids or not text.strip():
        return RedirectResponse("/publish?err=empty", status_code=302)

    # ─── جست‌وجو در Destination (نه SourceChannel!) ───
    dest_records = (await db.execute(
        select(Destination).where(Destination.chat_id.in_(dest_ids))
    )).scalars().all()
    title_map = {d.chat_id: d.title for d in dest_records}

    # ─── اختیاری: اعمال فیلترها + LLM اگر کاربر خواست ───
    final_text = text
    skip = False
    reason = ""

    if apply_filters == "1":
        filter_svc = FilterService(db)
        skip, reason = filter_svc.should_skip(text)

        if not skip:
            # LLM classify (اگر پرامپت فعال باشد)
            try:
                from app.services.llm import LLMService
                llm = LLMService()
                prompt_row = (await db.execute(
                    select(LLMPrompt).where(
                        LLMPrompt.prompt_type == "classify",
                        LLMPrompt.is_active.is_(True),
                        LLMPrompt.applies_to_chat_id.is_(None),
                    ).order_by(LLMPrompt.order)
                )).scalar_one_or_none()
                if prompt_row:
                    r = await llm.classify(text, prompt_row.prompt)
                    if r["is_spam"]:
                        skip = True
                        reason = f"llm_spam: {r['reason']}"

                # LLM clean (اگر پرامپت فعال باشد)
                if not skip:
                    clean_row = (await db.execute(
                        select(LLMPrompt).where(
                            LLMPrompt.prompt_type == "clean",
                            LLMPrompt.is_active.is_(True),
                            LLMPrompt.applies_to_chat_id.is_(None),
                        ).order_by(LLMPrompt.order)
                    )).scalar_one_or_none()
                    if clean_row:
                        final_text = await llm.clean(text, clean_row.prompt)

                # هدر/فوتر از FilterService
                if not skip:
                    final_text = filter_svc.apply_decorations(final_text)
            except Exception as e:
                # خطای LLM نباید ارسال را متوقف کند
                import logging
                logging.getLogger(__name__).warning("LLM filter failed: %s", e)

    # ─── ساخت پیام در صف برای هر مقصد ───
    created = 0
    for chat_id in dest_ids:
        db.add(MessageQueue(
            source_chat_id="0",
            source_message_id=0,
            dest_chat_id=chat_id,
            dest_chat_title=title_map.get(chat_id, chat_id),
            source_chat_title="✍️ انتشار دستی" + (f" ({project_name})" if project_name else ""),
            content_preview=text[:300],
            cleaned_text=final_text[:3000],
            status=MessageStatus.SPAM.value if skip else MessageStatus.PENDING.value,
            error_message=reason if skip else "",
            llm_reason="ad" if is_ad == "1" else "",
            manual_source=True,
        ))
        created += 1

    db.add(ActivityLog(
        user=u.username,
        action="انتشار دستی",
        detail=f"{created} مقصد | {project_name or '(بدون نام)'} | فیلتر={'بله' if apply_filters=='1' else 'خیر'}",
    ))
    await db.commit()
    return RedirectResponse("/messages", status_code=302)
