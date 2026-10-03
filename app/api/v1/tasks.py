from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.board import Board
from app.models.task import Task
from app.models.user import User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.core.deps import get_current_user, get_column_with_access, get_task_with_access, verify_workspace_membership

router = APIRouter()

@router.post("/columns/{column_id}/tasks", response_model=TaskResponse)
async def create_task(
    column_id: int,
    task_in: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    column = await get_column_with_access(column_id, current_user.id, db)
    if task_in.assignee_id is not None:
        board_result = await db.execute(select(Board).where(Board.id == column.board_id))
        board = board_result.scalar_one_or_none()
        await verify_workspace_membership(board.workspace_id, task_in.assignee_id, db)
    task = Task(title=task_in.title, description=task_in.description, position=task_in.position, column_id=column_id, assignee_id=task_in.assignee_id)
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task

@router.get("/columns/{column_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    column_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await get_column_with_access(column_id, current_user.id, db)
    tasks_result = await db.execute(select(Task).where(Task.column_id == column_id).order_by(Task.position))
    tasks = tasks_result.scalars().all()
    return tasks

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = await get_task_with_access(task_id, current_user.id, db)
    changes = task_in.model_dump(exclude_unset=True)
    series = {"title", "position", "column_id"}
    for key, value in changes.items():
        if key in series and value is None:
            raise HTTPException(status_code=422, detail="Validation Error, value is none!")
    task_column = changes.get("column_id", task.column_id)
    column =  await get_column_with_access(task_column, current_user.id, db)
    final_assignee = changes.get("assignee_id", task.assignee_id)
    if final_assignee is not None:
        board_result = await db.execute(select(Board).where(Board.id == column.board_id))
        board = board_result.scalar_one_or_none()
        await verify_workspace_membership(board.workspace_id,final_assignee, db)
    for key, value in changes.items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    task = await get_task_with_access(task_id, current_user.id, db)
    await db.delete(task)
    await db.commit()