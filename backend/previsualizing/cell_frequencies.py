"""Shapes Sample rows into the cell-population-frequency summary table."""

from sqlalchemy import Connection, select

from backend.models.tables import sample
from backend.schemas.cell_frequencies import CellFrequencyRow

POPULATIONS = ("b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte")


def get_cell_frequencies(conn: Connection) -> list[CellFrequencyRow]:
    rows = conn.execute(
        select(
            sample.c.source_id,
            sample.c.b_cell,
            sample.c.cd8_t_cell,
            sample.c.cd4_t_cell,
            sample.c.nk_cell,
            sample.c.monocyte,
        ).order_by(sample.c.id)
    ).all()

    result: list[CellFrequencyRow] = []
    for row in rows:
        counts = {population: getattr(row, population) for population in POPULATIONS}
        total_count = sum(counts.values())
        for population in POPULATIONS:
            count = counts[population]
            result.append(
                CellFrequencyRow(
                    sample=row.source_id,
                    population=population,
                    count=count,
                    total_count=total_count,
                    percentage=100 * count / total_count,
                )
            )
    return result
