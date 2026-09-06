"""FastAPI app entrypoint. Run with: uvicorn backend.main:app"""

from fastapi import FastAPI

from backend.api.routes.cell_frequencies import router as cell_frequencies_router

app = FastAPI(title="teiko")

app.include_router(cell_frequencies_router, prefix="/api")
