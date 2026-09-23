from fastapi import FastAPI
from app.api.v1.users import router as users_router
from app.api.v1.workspaces import router as workspace_router
from app import models  # noqa: F401
from app.api.v1.boards import router as boards_router
from app.api.v1.board_columns import router as board_columns_router

app = FastAPI()
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(workspace_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(boards_router, tags=["boards"])
app.include_router(board_columns_router, tags=["board_columns"])

@app.get("/health")
async def root():
    return {"status": "ok"}