from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.cli import _alembic_config
from app.database import Base, engine
import app.models  # noqa: F401  (registers every model on Base.metadata)


def test_database_is_at_head():
    script = ScriptDirectory.from_config(_alembic_config())
    with engine.connect() as connection:
        current = MigrationContext.configure(connection).get_current_heads()
    assert set(current) == set(script.get_heads())


def test_models_match_migrations():
    # A model change without a migration (or vice versa) shows up as a diff.
    with engine.connect() as connection:
        diff = compare_metadata(MigrationContext.configure(connection), Base.metadata)
    assert diff == []
