from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.workspace import Workspace
from app.models.workspace_member import WorkspaceMember
from app.models.user import User
from app.schemas.workspace import WorkspaceCreate, WorkspaceResponse, WorkspaceMemberCreate
from app.core.deps import get_current_user

router = APIRouter()

@router.post("/", response_model=WorkspaceResponse)
async def create_workspace(
    workspace_in: WorkspaceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    workspace = Workspace(name=workspace_in.name)
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    workspace_member = WorkspaceMember(user_id=current_user.id, workspace_id=workspace.id, role="owner")
    db.add(workspace_member)
    await db.commit()

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
    result = await db.execute(
    select(WorkspaceMember).where(
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.workspace_id == workspace_id
    )
)
    membership = result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(status_code=403, detail="Not a member of this workspace")
    else:
        workspace_result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        workspace = workspace_result.scalar_one_or_none()
        if workspace is None:
            raise HTTPException(status_code=404, detail="Not Found")
        else:
            return workspace
        
@router.post("/{workspace_id}/members", response_model=WorkspaceMemberCreate)
async def add_workspace_member(
    workspace_id: int,
    member_in: WorkspaceMemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
    select(WorkspaceMember).where(
        WorkspaceMember.user_id == current_user.id,
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.role == "owner"
        )
    )
    owner_check = result.scalar_one_or_none()

    if owner_check is None:
        raise HTTPException(status_code=403, detail="Not the owner of this workspace")
    
    workspace_member_result = await db.execute(select(WorkspaceMember).where(
        WorkspaceMember.user_id == member_in.user_id, 
        WorkspaceMember.workspace_id == workspace_id))
    
    workspace_member = workspace_member_result.scalar_one_or_none()

    if workspace_member is not None:
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