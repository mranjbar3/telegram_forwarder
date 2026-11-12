from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, ActivityLog, RolePermission
from app.api.auth import current_user, hash_pw

router = APIRouter()

def _require(request, user):
    if not user: return RedirectResponse("/auth/login")
    return None

@router.get("")
async def list_users(request: Request, db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    users = (await db.execute(select(User).order_by(User.id))).scalars().all()
    return templates.TemplateResponse("users.html", {"request": request, "users": users, "me": u})

@router.post("/create")
async def create_user(
    request: Request,
    username: str = Form(...), full_name: str = Form(""),
    password: str = Form(...), role: str = Form("viewer"),
    db: AsyncSession = Depends(get_db),
):
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    if (await db.execute(select(User).where(User.username == username))).scalar_one_or_none():
        return RedirectResponse("/users?err=dup", status_code=302)
    db.add(User(username=username, full_name=full_name, password_hash=hash_pw(password), role=role))
    db.add(ActivityLog(user=u.username, action="ایجاد کاربر", detail=username))
    await db.commit()
    return RedirectResponse("/users", status_code=302)

@router.post("/{uid}/toggle")
async def toggle_user(uid: int, request: Request, db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u or u.role != "admin": return RedirectResponse("/auth/login")
    target = await db.get(User, uid)
    if target and target.username != "admin":
        target.is_active = not target.is_active
        await db.commit()
    return RedirectResponse("/users", status_code=302)

@router.get("/roles")
async def roles_page(request: Request, role: str = "operator", db: AsyncSession = Depends(get_db)):
    from app.main import templates
    u = await current_user(request, db)
    if not u: return RedirectResponse("/auth/login")
    perms = (await db.execute(select(RolePermission).where(RolePermission.role == role))).scalars().all()
    role_names = (await db.execute(select(RolePermission.role).distinct())).scalars().all()
    return templates.TemplateResponse("roles.html", {
        "request": request, "role": role, "perms": [p.page for p in perms],
        "role_names": role_names,
    })

@router.post("/roles/save")
async def save_role(request: Request, role: str = Form(...), pages: list[str] = Form([]),
                    db: AsyncSession = Depends(get_db)):
    u = await current_user(request, db)
    if not u or u.role != "admin": return RedirectResponse("/auth/login")
    await db.execute(RolePermission.__table__.delete().where(RolePermission.role == role))
    for p in pages:
        db.add(RolePermission(role=role, page=p))
    await db.commit()
    return RedirectResponse(f"/users/roles?role={role}", status_code=302)
