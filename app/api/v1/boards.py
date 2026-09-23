from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.board import Board
from app.models.user import User
from app.schemas.board import BoardCreate, BoardResponse
from app.core.deps import get_current_user, verify_workspace_membership

router = APIRouter()

@router.post("/workspaces/{workspace_id}/boards", response_model=BoardResponse)
async def create_board(
    workspace_id: int,
    board_in: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await verify_workspace_membership(workspace_id, current_user.id, db)
    board = Board(name=board_in.name, workspace_id=workspace_id)
    db.add(board)
    await db.commit()
    await db.refresh(board)
    return board

@router.get("/workspaces/{workspace_id}/boards", response_model=list[BoardResponse])
async def list_boards(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    await verify_workspace_membership(workspace_id, current_user.id, db)
    result = await db.execute(select(Board).where(Board.workspace_id == workspace_id))
    all_results = result.scalars().all()
    return all_results
    