#!/usr/bin/env python3
"""Exports the FastAPI app's OpenAPI schema to frontend/openapi.json.

frontend/src/types/api.ts is generated from that file via `npm run gen:types`
(openapi-typescript), so frontend request/response types stay in sync with
the backend without being hand-maintained. Re-run both steps after changing
any route's request/response shape.
"""

import json

from backend.core.config import REPO_ROOT
from backend.main import app

OUTPUT_PATH = REPO_ROOT / "frontend" / "openapi.json"


def main() -> None:
    OUTPUT_PATH.write_text(json.dumps(app.openapi(), indent=2))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
