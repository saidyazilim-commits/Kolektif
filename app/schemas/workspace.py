from pydantic import ConfigDict, BaseModel, Field
import datetime
from typing import Literal


class WorkspaceCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name : str = Field(min_length=1)

class WorkspaceResponse(BaseModel):
    id : int
    name : str
    created_at : datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class WorkspaceMemberCreate(BaseModel):
    user_id : int
    role : Literal["owner", "member"]

class WorkspaceUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    name : str = Field(min_length=1)