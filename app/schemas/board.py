from pydantic import ConfigDict, BaseModel, Field
import datetime

class BoardCreate(BaseModel):
    name : str

class BoardResponse(BaseModel):
    id : int
    name : str
    workspace_id : int
    created_at : datetime.datetime
    model_config = ConfigDict(from_attributes=True)

class BoardUpdate(BaseModel):
    name : str = Field(min_length=1)