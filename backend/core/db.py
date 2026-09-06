"""Database engine setup for the teiko backend."""

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine

from backend.core.config import DATABASE_URL, DB_PATH, REPO_ROOT

engine = create_engine(DATABASE_URL)


def init_db() -> None:
    """Bring the database up to the latest migration, creating it first if needed."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    alembic_cfg = Config(str(REPO_ROOT / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
