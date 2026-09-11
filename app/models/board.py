from app.db.base import Base
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.workspace import Workspace
    from app.models.board_column import BoardColumn

class Board(Base):
    __tablename__ = "boards"

    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    workspace_id : Mapped[int] = mapped_column(ForeignKey("workspaces.id"))
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    workspace: Mapped["Workspace"] = relationship(back_populates="boards")
    columns: Mapped[list["BoardColumn"]] = relationship(back_populates="board")