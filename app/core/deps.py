from app.models.task import Task
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.board import Board
from app.models.board_column import BoardColumn
from app.models.user import User
from app.core.config import settings
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"})
        token_data = await db.execute(select(User).where(User.email == username))
        user = token_data.scalar_one_or_none()
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    if user is None:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    else:
        return user
    
async def verify_workspace_membership(workspace_id: int, user_id: int, db: AsyncSession) -> WorkspaceMember:
    result = await db.execute(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    return membership

async def get_workspace_or_404(workspace_id: int, db: AsyncSession) -> Workspace:
    result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace

async def get_membership_or_none(workspace_id: int, user_id: int, db: AsyncSession) -> WorkspaceMember | None:
    result = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id))
    return result.scalar_one_or_none()

async def get_board_or_404(board_id: int, db: AsyncSession) -> Board:
    result = await db.execute(select(Board).where(Board.id == board_id))
    board = result.scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return board

async def get_column_or_404(column_id: int, db: AsyncSession) -> BoardColumn:
    result = await db.execute(select(BoardColumn).where(BoardColumn.id == column_id))
    column = result.scalar_one_or_none()
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")
    return column

async def get_column_with_access(column_id: int, user_id: int, db: AsyncSession) -> BoardColumn:
    column = await get_column_or_404(column_id, db)
    
    board = await get_board_or_404(column.board_id, db)
    await verify_workspace_membership(board.workspace_id, user_id, db)
    return column

async def get_task_with_access(task_id: int, user_id: int, db: AsyncSession) -> Task:
    task_result = await db.execute(select(Task).where(Task.id == task_id))
    task = task_result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await get_column_with_access(task.column_id, user_id, db)
    return task

async def verify_workspace_owner(workspace_id: int, user_id: int, db: AsyncSession) -> WorkspaceMember:
    membership = await verify_workspace_membership(workspace_id, user_id, db)
    if membership.role != "owner":
        raise HTTPException(status_code=403, detail="Owner role required")
    return membership