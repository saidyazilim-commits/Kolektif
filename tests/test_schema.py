from app.db.base import Base
from app import models  # noqa: F401


def test_foreign_keys_have_predictable_names():
    tasks_fks = {fk.name for fk in Base.metadata.tables["tasks"].foreign_key_constraints}
    assert tasks_fks == {"tasks_assignee_id_fkey", "tasks_column_id_fkey"}

    columns_fks = {fk.name for fk in Base.metadata.tables["board_columns"].foreign_key_constraints}
    assert columns_fks == {"board_columns_board_id_fkey"}
    assert Base.metadata.tables["users"].primary_key.name == "users_pkey"