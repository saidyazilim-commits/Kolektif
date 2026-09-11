from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password
from app.schemas.user import UserLogin, Token
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=UserResponse)
async def register_user(user_in: UserCreate, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="Email already registered")
   
    hashed_pw = hash_password(user_in.password)
    new_user = User(email=user_in.email, hashed_password=hashed_pw)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

@router.post("/login", response_model=Token)
async def login_user(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    if existing_user is None:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    check_pw = verify_password(user_in.password, existing_user.hashed_password)
    if check_pw:
        token = create_access_token(data={"sub": existing_user.email})
        return Token(access_token=token, token_type="bearer")
    else:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user : User = Depends(get_current_user)):
    return current_user