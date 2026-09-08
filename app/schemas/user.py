from pydantic import BaseModel, ConfigDict
import datetime


class UserCreate(BaseModel):
    email : str
    password : str

class UserResponse(BaseModel):
    id : int 
    email : str
    is_active : bool
    created_at : datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class UserLogin(BaseModel):
    email : str
    password : str

class Token(BaseModel):
    access_token : str
    token_type : str
