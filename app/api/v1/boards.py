from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.board import Board
from app.models.user import User
from app.schemas.board import BoardCreate, BoardResponse, BoardUpdate
from app.core.deps import get_board_or_404, get_column_or_404, get_current_user, get_workspace_or_404, verify_workspace_membership, verify_workspace_owner
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
    workspace = await get_workspace_or_404(workspace_id, db)

    await verify_workspace_membership(workspace.id, current_user.id, db)
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
    workspace = await get_workspace_or_404(workspace_id, db)

    await verify_workspace_membership(workspace.id, current_user.id, db)
    result = await db.execute(select(Board).where(Board.workspace_id == workspace_id))
    all_results = result.scalars().all()
    return all_results
    
@router.delete("/boards/{board_id}", status_code=204)
async def delete_board(
    board_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    board = await get_board_or_404(board_id, db)

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
    board = await get_board_or_404(board_id, db)

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
    column = await get_column_or_404(column_id, db)

    # 1. kolonun board'unu bul
    board = await get_board_or_404(column.board_id, db)

    # 2. üye mi? (workspace id'si board'dan gelir)
    await verify_workspace_membership(board.workspace_id, current_user.id, db)

    # 3. ismi değiştir, kaydet, yenile, döndür
    column.name = column_in.name
    await db.commit()
    await db.refresh(column)
    return column

@router.delete("/columns/{column_id}", status_code=204)
async def delete_column(column_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    column = await get_column_or_404(column_id, db)
    board = await get_board_or_404(column.board_id, db)
    await verify_workspace_owner(board.workspace_id, current_user.id, db)
    await db.delete(column)
    await db.commit()