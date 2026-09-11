from app.db.base import Base
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.orm import mapped_column, Mapped, relationship
import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.task import Task

class User(Base):
    __tablename__ = "users"

    id : Mapped[int] = mapped_column(Integer, primary_key=True)
    email : Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    hashed_password : Mapped[str] = mapped_column(String, nullable=False)
    is_active : Mapped[bool] = mapped_column(Boolean, default=True)
    created_at : Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.now)
    assigned_tasks: Mapped[list["Task"]] = relationship(back_populates="assignee")