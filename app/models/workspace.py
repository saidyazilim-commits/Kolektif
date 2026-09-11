from app.db.base import Base
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.board import Board

class Workspace(Base):
    __tablename__ = "workspaces"

    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    boards: Mapped[list["Board"]] = relationship(back_populates="workspace")