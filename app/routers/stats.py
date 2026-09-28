from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_project_or_404
from app.database import get_db
from app.models import Project, Task, TaskStatus, User
from app.schemas import OverviewStats, ProjectStats

router = APIRouter(prefix="/stats", tags=["Statistics"])


async def scalar_count(db: AsyncSession, stmt) -> int:
    return int((await db.execute(stmt)).scalar_one())


@router.get("/overview", response_model=OverviewStats)
async def overview(db: AsyncSession = Depends(get_db)) -> OverviewStats:
    users = await scalar_count(db, select(func.count()).select_from(User))
    projects = await scalar_count(db, select(func.count()).select_from(Project))
    tasks = await scalar_count(db, select(func.count()).select_from(Task))
    pending = await scalar_count(db, select(func.count()).select_from(Task).where(Task.status == TaskStatus.pending))
    in_progress = await scalar_count(db, select(func.count()).select_from(Task).where(Task.status == TaskStatus.in_progress))
    completed = await scalar_count(db, select(func.count()).select_from(Task).where(Task.status == TaskStatus.completed))
    return OverviewStats(users=users, projects=projects, tasks=tasks, pending_tasks=pending, in_progress_tasks=in_progress, completed_tasks=completed)


@router.get("/projects/{project_id}", response_model=ProjectStats)
async def project_stats(project_id: int, db: AsyncSession = Depends(get_db)) -> ProjectStats:
    await get_project_or_404(db, project_id)
    base = select(func.count()).select_from(Task).where(Task.project_id == project_id)
    total = await scalar_count(db, base)
    pending = await scalar_count(db, base.where(Task.status == TaskStatus.pending))
    in_progress = await scalar_count(db, base.where(Task.status == TaskStatus.in_progress))
    completed = await scalar_count(db, base.where(Task.status == TaskStatus.completed))
    return ProjectStats(project_id=project_id, total_tasks=total, pending_tasks=pending, in_progress_tasks=in_progress, completed_tasks=completed)
