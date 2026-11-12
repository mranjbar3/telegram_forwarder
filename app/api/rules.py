from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import FilterRule
from app.api.auth import require_login

router = APIRouter()

@router.get("")
async def rules_page(request: Request, db: AsyncSession = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/auth/login")
    from app.main import templates
    rules = (await db.execute(select(FilterRule))).scalars().all()
    return templates.TemplateResponse("rules.html", {"request": request, "rules": rules})

@router.post("/create")
async def create_rule(
    name: str = Form(...), rule_type: str = Form(...), pattern: str = Form(...),
    request: Request = None, db: AsyncSession = Depends(get_db),
):
    if not request.session.get("logged_in"):
        return RedirectResponse("/auth/login")
    db.add(FilterRule(name=name, rule_type=rule_type, pattern=pattern))
    await db.commit()
    return RedirectResponse("/rules", status_code=302)

@router.post("/{rule_id}/delete")
async def delete_rule(rule_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    if not request.session.get("logged_in"):
        return RedirectResponse("/auth/login")
    rule = await db.get(FilterRule, rule_id)
    if rule:
        await db.delete(rule)
        await db.commit()
    return RedirectResponse("/rules", status_code=302)
