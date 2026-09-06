"""Runtime configuration for the teiko backend."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = Path(os.environ.get("TEIKO_DB_PATH", REPO_ROOT / "data" / "teiko.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"
