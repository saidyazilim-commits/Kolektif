from pydantic import BaseModel, ConfigDict
import datetime
from pydantic import ConfigDict, BaseModel, EmailStr, Field
from pydantic import field_validator

class UserCreate(BaseModel):
    email : EmailStr
    password : str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must be at most 72 bytes")
        return value

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
