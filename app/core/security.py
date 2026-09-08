import bcrypt
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.core.config import settings

def hash_password(password: str) -> str:
    password = password.encode("utf-8")
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    password = hashed.decode("utf-8")
    return password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    plain_password = plain_password.encode("utf-8")
    hashed_password = hashed_password.encode("utf-8")
    
    if bcrypt.checkpw(plain_password, hashed_password):
        print("It Matches!")
        return True
    else:
        print("It Does not Match :(")
        return False
    
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt