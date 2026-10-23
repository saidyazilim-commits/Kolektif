from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.board import Board
from app.models.board_column import BoardColumn
from app.models.user import User
from app.schemas.board import BoardCreate, BoardResponse
from app.core.deps import get_current_user, verify_workspace_membership, verify_workspace_owner

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
    
@router.delete("/boards/{board_id}", status_code=204)
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    board_result = await db.execute(select(Board).where(Board.id == board_id))
    board = board_result.scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")

    await verify_workspace_owner(board.workspace_id, current_user.id, db)

    await db.delete(board)
    await db.commit()

@router.delete("/columns/{column_id}", status_code=204)
async def delete_column(column_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    column_result = await db.execute(select(BoardColumn).where(BoardColumn.id == column_id))
    column = column_result.scalar_one_or_none()
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found") 
    board_result = await db.execute(select(Board).where(Board.id == column.board_id))
    board = board_result.scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")
    await verify_workspace_owner(board.workspace_id, current_user.id, db)
    await db.delete(column)
    await db.commit()