from pydantic import ConfigDict, BaseModel
import datetime

class BoardCreate(BaseModel):
    name : str

class BoardResponse(BaseModel):
    id : int
    name : str
    workspace_id : int
    created_at : datetime.datetime
    model_config = ConfigDict(from_attributes=True)