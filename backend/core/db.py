"""Database engine setup for the teiko backend."""

from sqlalchemy import create_engine

from backend.core.config import DATABASE_URL, DB_PATH
from backend.models.tables import metadata

engine = create_engine(DATABASE_URL)


def init_db() -> None:
    """Create all tables that don't already exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    metadata.create_all(engine)
