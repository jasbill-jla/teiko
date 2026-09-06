"""Pydantic response shapes for the cell-frequencies endpoint."""

from pydantic import BaseModel


class CellFrequencyRow(BaseModel):
    sample: str
    population: str
    count: int
    total_count: int
    percentage: float
