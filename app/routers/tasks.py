from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_project_or_404, get_user_or_404
from app.database import get_db
from app.models import Task, TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskRead, TaskStatusUpdate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["Tasks"])


async def get_task_or_404(db: AsyncSession, task_id: int) -> Task:
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


async def validate_task_relations(db: AsyncSession, project_id: int | None = None, assignee_id: int | None = None) -> None:
    if project_id is not None:
        await get_project_or_404(db, project_id)
    if assignee_id is not None:
        await get_user_or_404(db, assignee_id)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(payload: TaskCreate, db: AsyncSession = Depends(get_db)) -> Task:
    await validate_task_relations(db, payload.project_id, payload.assignee_id)
    task = Task(**payload.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@router.get("", response_model=list[TaskRead])
async def list_tasks(project_id: int | None = Query(default=None, gt=0), assignee_id: int | None = Query(default=None, gt=0), task_status: TaskStatus | None = Query(default=None, alias="status"), priority: TaskPriority | None = Query(default=None), due_before: date | None = Query(default=None), skip: int = Query(default=0, ge=0), limit: int = Query(default=20, ge=1, le=100), db: AsyncSession = Depends(get_db)) -> list[Task]:
    stmt = select(Task).order_by(Task.id.desc())
    if project_id is not None:
        stmt = stmt.where(Task.project_id == project_id)
    if assignee_id is not None:
        stmt = stmt.where(Task.assignee_id == assignee_id)
    if task_status is not None:
        stmt = stmt.where(Task.status == task_status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if due_before is not None:
        stmt = stmt.where(Task.due_date <= due_before)
    stmt = stmt.offset(skip).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)) -> Task:
    return await get_task_or_404(db, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, payload: TaskUpdate, db: AsyncSession = Depends(get_db)) -> Task:
    task = await get_task_or_404(db, task_id)
    updates = payload.model_dump(exclude_unset=True)
    await validate_task_relations(db, updates.get("project_id"), updates.get("assignee_id"))
    for field, value in updates.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


@router.patch("/{task_id}/status", response_model=TaskRead)
async def update_task_status(task_id: int, payload: TaskStatusUpdate, db: AsyncSession = Depends(get_db)) -> Task:
    task = await get_task_or_404(db, task_id)
    task.status = payload.status
    await db.commit()
    await db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)) -> Response:
    task = await get_task_or_404(db, task_id)
    await db.delete(task)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
