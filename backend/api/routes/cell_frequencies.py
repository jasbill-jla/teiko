from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from backend.core.db import get_connection
from backend.crunching.cell_frequencies import get_cell_frequencies
from backend.schemas.cell_frequencies import CellFrequencyRow

router = APIRouter()


@router.get("/cell-frequencies", response_model=list[CellFrequencyRow])
def read_cell_frequencies(
    conn: Connection = Depends(get_connection),
) -> list[CellFrequencyRow]:
    return get_cell_frequencies(conn)
