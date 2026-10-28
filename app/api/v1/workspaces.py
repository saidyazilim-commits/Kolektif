from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceMemberCreate, WorkspaceUpdate
from app.core.deps import get_current_user, get_membership_or_none, get_workspace_or_404, verify_workspace_owner, verify_workspace_membership

router = APIRouter()

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = Workspace(name=workspace_in.name)
    db.add(workspace)
    await db.flush()

    workspace_member = WorkspaceMember(user_id=current_user.id, workspace_id=workspace.id, role="owner")
    db.add(workspace_member)
    await db.commit()
    await db.refresh(workspace)


    return workspace

@router.get("/", response_model=list[WorkspaceResponse])
async def list_my_workspaces(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == current_user.id)
    )
    workspace = result.scalars().all()

    return workspace

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. workspace'i bul
    workspace = await get_workspace_or_404(workspace_id, db)

    # 2. üye kontrolü
    await verify_workspace_membership(workspace.id, current_user.id, db)

    return workspace  

@router.post("/{workspace_id}/members", response_model=WorkspaceMemberCreate)
async def add_workspace_member(
    workspace_id: int,
    member_in: WorkspaceMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. workspace'i bul; yoksa 404 "Workspace not found"
    workspace = await get_workspace_or_404(workspace_id, db)

    # 2. owner kontrolü 
    await verify_workspace_owner(workspace.id, current_user.id, db)

    # 3. eklenecek kullanıcı kontrolü, yoksa 404 "User not found"
    user_result = await db.execute(select(User).where(User.id == member_in.user_id))
    user = user_result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_member = await get_membership_or_none(workspace_id, member_in.user_id, db)
    if existing_member is not None:
        raise HTTPException(status_code=400, detail="User is already a member")

    new_member = WorkspaceMember(
        user_id=member_in.user_id,
        workspace_id=workspace_id,
        role=member_in.role
    )
    
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)
    return new_member

@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. workspace'i bul; yoksa 404 "Workspace not found"
    workspace = await get_workspace_or_404(workspace_id, db)
    
    # 2. owner kontrolü
    await verify_workspace_owner(workspace.id, current_user.id, db)
    # 3. sil + kaydet
    await db.delete(workspace)
    await db.commit()
    
@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def rename_workspace(
    workspace_id: int,
    workspace_in: WorkspaceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. workspace'i bul; yoksa 404 "Workspace not found"
    workspace = await get_workspace_or_404(workspace_id, db)
    # 2. üye kontrolü yap workspace.id ile
    await verify_workspace_membership(workspace.id, current_user.id, db)
    # 3. adı güncelle, kaydet, güncel hâli yenile
    workspace.name = workspace_in.name
    await db.commit()
    await db.refresh(workspace)
    # 4. güncellenmiş workspace'i döndür
    return workspace