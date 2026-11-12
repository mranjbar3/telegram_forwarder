from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import LLMPrompt
from app.api.auth import require_login

router = APIRouter()

@router.get("")
async def prompts_page(request: Request, db: AsyncSession = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/auth/login")
    from app.main import templates
    prompts = (await db.execute(
        select(LLMPrompt).order_by(LLMPrompt.prompt_type, LLMPrompt.order)
    )).scalars().all()
    return templates.TemplateResponse("prompts.html", {"request": request, "prompts": prompts})

@router.post("/create")
async def create_prompt(
    name: str = Form(...),
    prompt_type: str = Form(...),
    prompt: str = Form(...),
    applies_to_chat_id: str = Form(""),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    if not request.session.get("logged_in"):
        return RedirectResponse("/auth/login")
    chat_id = int(applies_to_chat_id) if applies_to_chat_id.strip() else None
    db.add(LLMPrompt(
        name=name, prompt_type=prompt_type, prompt=prompt,
        applies_to_chat_id=chat_id,
    ))
    await db.commit()
    return RedirectResponse("/prompts", status_code=302)

@router.post("/{pid}/delete")
async def delete_prompt(pid: int, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/auth/login")
    p = await db.get(LLMPrompt, pid)
    if p:
        await db.delete(p)
        await db.commit()
    return RedirectResponse("/prompts", status_code=302)
