from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey"
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)