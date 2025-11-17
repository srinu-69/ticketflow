from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from . import crud, schemas
from .database import get_session

router = APIRouter(prefix="/timeline", tags=["timeline"])


@router.post("/projects", response_model=schemas.ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(payload: schemas.ProjectCreate, db: AsyncSession = Depends(get_session)):
    project = await crud.create_project(db, name=payload.name)
    return project


@router.get("/projects", response_model=list[schemas.ProjectRead])
async def list_projects(db: AsyncSession = Depends(get_session)):
    projects = await crud.list_projects(db)
    return projects


@router.get("/projects/{project_id}", response_model=schemas.ProjectWithTasks)
async def get_project(project_id: int, db: AsyncSession = Depends(get_session)):
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # pydantic will convert tasks automatically (from_attributes)
    return project


@router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_session)):
    await crud.delete_project(db, project_id)
    return None


# Tasks
@router.post("/tasks", response_model=schemas.TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(payload: schemas.TaskCreate, db: AsyncSession = Depends(get_session)):
    # ensure project exists
    proj = await crud.get_project(db, payload.project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    task = await crud.create_task(db, payload)
    return task


@router.get("/projects/{project_id}/tasks", response_model=list[schemas.TaskRead])
async def list_tasks(project_id: int, db: AsyncSession = Depends(get_session)):
    # If project not found, return empty list or 404 — choose 404 for clarity
    proj = await crud.get_project(db, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    tasks = await crud.list_tasks_for_project(db, project_id)
    return tasks


@router.patch("/tasks/{task_id}", response_model=schemas.TaskRead)
async def patch_task(task_id: int, payload: schemas.TaskUpdate, db: AsyncSession = Depends(get_session)):
    task = await crud.update_task(db, task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_task(task_id: int, db: AsyncSession = Depends(get_session)):
    await crud.delete_task(db, task_id)
    return None


@router.get("", response_model=schemas.TimelineTicketResponse)
async def list_timeline(db: AsyncSession = Depends(get_session)):
    return await crud.list_ticket_timeline_tasks(db)


@router.get("/tickets", response_model=schemas.TimelineTicketResponse)
async def list_ticket_timeline(db: AsyncSession = Depends(get_session)):
    return await crud.list_ticket_timeline_tasks(db)


@router.get("/stats", response_model=schemas.TimelineStats)
async def timeline_stats(db: AsyncSession = Depends(get_session)):
    return await crud.get_timeline_stats(db)
