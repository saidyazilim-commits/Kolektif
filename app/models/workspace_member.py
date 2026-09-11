from app.db.base import Base
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.workspace import Workspace

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"))
    workspace_id : Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    role: Mapped[str] = mapped_column(String, nullable=False)
    joined_at : Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    user: Mapped["User"] = relationship()
    workspace: Mapped["Workspace"] = relationship()