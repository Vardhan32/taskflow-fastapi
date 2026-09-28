from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import ensure_email_available, get_user_or_404
from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    await ensure_email_available(db, payload.email)
    user = User(**payload.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("", response_model=list[UserRead])
async def list_users(skip: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)) -> list[User]:
    stmt = select(User).order_by(User.id).offset(skip).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)) -> User:
    return await get_user_or_404(db, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)) -> User:
    user = await get_user_or_404(db, user_id)
    updates = payload.model_dump(exclude_unset=True)
    if "email" in updates:
        await ensure_email_available(db, updates["email"], exclude_user_id=user_id)
    for field, value in updates.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    user = await get_user_or_404(db, user_id)
    await db.delete(user)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
