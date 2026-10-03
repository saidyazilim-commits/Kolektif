import datetime
from typing import Optional

from pydantic import ConfigDict, BaseModel


class TaskCreate(BaseModel):
    title : str
    description : Optional[str] = None
    position : int
    assignee_id : Optional[int] = None

class TaskResponse(BaseModel):
    id : int
    title : str
    description : Optional[str] = None
    column_id : int
    assignee_id : Optional[int] = None
    position : int
    created_at : datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class TaskUpdate(BaseModel):
    title : Optional[str] = None
    description : Optional[str] = None
    position : Optional[int] = None
    column_id : Optional[int] = None
    assignee_id : Optional[int] = None
    