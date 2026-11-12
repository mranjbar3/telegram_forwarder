from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import SourceChannel
from app.api.auth import current_user

router = APIRouter()

@router.get("")
async def categories_page(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    rows = await db.execute(
        select(SourceChannel.category, func.count())
        .group_by(SourceChannel.category)
    )
    return templates.TemplateResponse("categories.html", {
        "request": request, "cats": list(rows.all()),
    })
