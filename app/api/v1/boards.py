from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.board import Board
from app.models.board_column import BoardColumn
from app.models.user import User
from app.models.workspace import Workspace
from app.schemas.board import BoardCreate, BoardResponse, BoardUpdate
from app.core.deps import get_current_user, verify_workspace_membership, verify_workspace_owner
from app.schemas.board_column import BoardColumnResponse, BoardColumnUpdate

router = APIRouter()

@router.post("/workspaces/{workspace_id}/boards", response_model=BoardResponse)
async def create_board(
    workspace_id: int,
    board_in: BoardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. workspace'i bul; yoksa 404 "Workspace not found"
    workspace_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = workspace_result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

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
    # 1. workspace'i bul; yoksa 404 "Workspace not found"
    workspace_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
    workspace = workspace_result.scalar_one_or_none()
    if workspace is None:
        raise HTTPException(status_code=404, detail="Workspace not found")

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

@router.patch("/boards/{board_id}", response_model=BoardResponse)
async def rename_board(
    board_id: int,
    board_in: BoardUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. board'u bul
    board_result = await db.execute(select(Board).where(Board.id == board_id))
    board = board_result.scalar_one_or_none()

    # 2. yoksa 404, 
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")

    # 3. üye mi kontrolü
    await verify_workspace_membership(board.workspace_id, current_user.id, db)

    # 4. ismi değiştir, kaydet, yenile, döndür
    board.name = board_in.name
    await db.commit()
    await db.refresh(board)
    return board

@router.patch("/columns/{column_id}", response_model=BoardColumnResponse)
async def rename_column(
    column_id: int,
    column_in: BoardColumnUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. kolonu bul
    column_result = await db.execute(select(BoardColumn).where(BoardColumn.id == column_id))
    column = column_result.scalar_one_or_none()
    if column is None:
        raise HTTPException(status_code=404, detail="Column not found")

    # 2. kolonun board'unu bul
    board_result = await db.execute(select(Board).where(Board.id == column.board_id))
    board = board_result.scalar_one_or_none()
    if board is None:
        raise HTTPException(status_code=404, detail="Board not found")

    # 3. üye mi? (workspace id'si board'dan gelir)
    await verify_workspace_membership(board.workspace_id, current_user.id, db)

    # 4. ismi değiştir, kaydet, yenile, döndür
    column.name = column_in.name
    await db.commit()
    await db.refresh(column)
    return column

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