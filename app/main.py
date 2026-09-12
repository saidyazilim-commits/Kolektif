from fastapi import FastAPI
from app.api.v1.users import router as users_router
from app.api.v1.workspaces import router as workspace_router
from app import models  # noqa: F401

app = FastAPI()
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(workspace_router, prefix="/workspaces", tags=["workspaces"])


@app.get("/health")
async def root():
    return {"status": "ok"}