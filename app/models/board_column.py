from app.db.base import Base
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column,relationship
from typing import TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from app.models.board import Board
    from app.models.task import Task

class BoardColumn(Base):
    __tablename__ = "board_columns"

    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    name : Mapped[str] = mapped_column(String, nullable=False)
    board_id : Mapped[int] = mapped_column(ForeignKey("boards.id"))
    position : Mapped[int] = mapped_column(Integer)
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    board: Mapped["Board"] = relationship(back_populates="columns")
    tasks: Mapped[list["Task"]] = relationship(back_populates="column")