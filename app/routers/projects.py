from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_project_or_404, get_user_or_404
from app.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Project:
    await get_user_or_404(db, payload.owner_id)
    project = Project(**payload.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=list[ProjectRead])
async def list_projects(owner_id: int | None = Query(default=None, gt=0), skip: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)) -> list[Project]:
    stmt = select(Project).order_by(Project.id)
    if owner_id is not None:
        stmt = stmt.where(Project.owner_id == owner_id)
    stmt = stmt.offset(skip).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)) -> Project:
    return await get_project_or_404(db, project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(project_id: int, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)) -> Project:
    project = await get_project_or_404(db, project_id)
    updates = payload.model_dump(exclude_unset=True)
    if "owner_id" in updates:
        await get_user_or_404(db, updates["owner_id"])
    for field, value in updates.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    project = await get_project_or_404(db, project_id)
    await db.delete(project)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
