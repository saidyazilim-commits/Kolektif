from pydantic import ConfigDict, BaseModel
import datetime
from typing import Literal

class WorkspaceCreate(BaseModel):
    name : str

class WorkspaceResponse(BaseModel):
    id : int
    name : str
    created_at : datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class WorkspaceMemberCreate(BaseModel):
    user_id : int
    role : Literal["owner", "member"]