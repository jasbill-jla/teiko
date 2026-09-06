"""FastAPI app entrypoint. Run with: uvicorn backend.main:app"""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.routes.cell_frequencies import router as cell_frequencies_router
from backend.api.routes.response_frequency_analysis import (
    router as response_frequency_analysis_router,
)
from backend.api.routes.samples import router as samples_router
from backend.core.config import REPO_ROOT

app = FastAPI(title="teiko")

# /api/cell-frequencies is ~6MB of repetitive JSON uncompressed -- over
# Codespaces' port-forwarding tunnel (a real network hop, not loopback) that
# dominates page load. gzip shrinks it several-fold for negligible CPU cost.
app.add_middleware(GZipMiddleware)

app.include_router(cell_frequencies_router, prefix="/api")
app.include_router(response_frequency_analysis_router, prefix="/api")
app.include_router(samples_router, prefix="/api")

# Registered after the API routes, so /api/* always resolves to them first.
# Only present once `npm run build` has produced a frontend/dist -- absent in
# backend-only contexts like the test suite, so this is skipped rather than
# mounting a directory that doesn't exist.
FRONTEND_DIST = REPO_ROOT / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
