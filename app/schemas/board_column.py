from pydantic import ConfigDict, BaseModel
import datetime

class BoardColumnCreate(BaseModel):
    name : str
    position : int

class BoardColumnResponse(BaseModel):
    id : int
    name : str
    board_id : int
    position : int
    created_at : datetime.datetime

    model_config = ConfigDict(from_attributes=True)