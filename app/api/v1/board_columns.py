from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.board import Board
from app.models.board_column import BoardColumn
from app.models.user import User
from app.schemas.board_column import BoardColumnCreate, BoardColumnResponse
from app.core.deps import get_current_user, verify_workspace_membership

router = APIRouter()

@router.post("/boards/{board_id}/columns", response_model=BoardColumnResponse)
async def create_column(
    board_id: int,
    column_in: BoardColumnCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    board_result = await db.execute(select(Board).where(Board.id == board_id))
    board = board_result.scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board Not Found!")
    await verify_workspace_membership(board.workspace_id, current_user.id, db)
    boardColumn = BoardColumn(name=column_in.name, position=column_in.position, board_id=board_id)
    db.add(boardColumn)
    await db.commit()
    await db.refresh(boardColumn)
    return boardColumn

@router.get("/boards/{board_id}/columns", response_model=list[BoardColumnResponse])
async def list_columns(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    board_result = await db.execute(select(Board).where(Board.id == board_id))
    board = board_result.scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board Not Found")
    await verify_workspace_membership(board.workspace_id, current_user.id, db)
    columns_result = await db.execute(select(BoardColumn).where(BoardColumn.board_id == board_id))
    columns = columns_result.scalars().all()
    return columns