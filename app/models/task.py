from app.db.base import Base
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.board_column import BoardColumn
    from app.models.user import User

class Task(Base):
    __tablename__ = "tasks"

    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    title : Mapped[str] = mapped_column(String, nullable=False)
    description : Mapped[str] = mapped_column(String, nullable=True)
    column_id : Mapped[int] = mapped_column(ForeignKey("board_columns.id"))
    assignee_id : Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    position : Mapped[int] = mapped_column(Integer)
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    column: Mapped["BoardColumn"] = relationship(back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship(back_populates="assigned_tasks")