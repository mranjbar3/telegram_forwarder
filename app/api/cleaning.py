from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import FilterRule, LLMPrompt, ActivityLog
from app.api.auth import current_user

router = APIRouter()


@router.get("")
async def cleaning_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u:
        return RedirectResponse("/auth/login")
    rules = (await db.execute(select(FilterRule).order_by(FilterRule.id))).scalars().all()
    prompts = (await db.execute(
        select(LLMPrompt).order_by(LLMPrompt.prompt_type, LLMPrompt.order)
    )).scalars().all()
    return templates.TemplateResponse("cleaning.html", {
        "request": request, "active": "cleaning", "rules": rules, "prompts": prompts,
    })


# ─── rules ───
@router.post("/rules/create")
async def create_rule(
    request: Request, name: str = Form(...), rule_type: str = Form(...),
    pattern: str = Form(...), db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    db.add(FilterRule(name=name, rule_type=rule_type, pattern=pattern))
    await db.commit()
    return RedirectResponse("/cleaning#rules", status_code=302)


@router.post("/rules/{rid}/delete")
async def delete_rule(rid: int, request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    r = await db.get(FilterRule, rid)
    if r:
        await db.delete(r); await db.commit()
    return RedirectResponse("/cleaning#rules", status_code=302)


# ─── prompts ───
@router.post("/prompts/create")
async def create_prompt(
    request: Request, name: str = Form(...), prompt_type: str = Form(...),
    prompt: str = Form(...), applies_to_chat_id: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    cid = int(applies_to_chat_id) if applies_to_chat_id.strip() else None
    db.add(LLMPrompt(name=name, prompt_type=prompt_type, prompt=prompt, applies_to_chat_id=cid))
    await db.commit()
    return RedirectResponse("/cleaning#prompts", status_code=302)


@router.post("/prompts/{pid}/delete")
async def delete_prompt(pid: int, request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    p = await db.get(LLMPrompt, pid)
    if p:
        await db.delete(p); await db.commit()
    return RedirectResponse("/cleaning#prompts", status_code=302)
