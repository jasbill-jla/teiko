#!/usr/bin/env python3
"""Initializes the database schema and loads all rows from the cell-count CSV.

Schema setup is delegated to Alembic (via backend.core.db.init_db) rather
than reimplemented here. Re-running this script wipes and reloads all three
tables from the CSV, so it's safe to run more than once.
"""

import csv
from pathlib import Path

from sqlalchemy import delete, insert

from backend.core.db import engine, init_db
from backend.models.tables import project, sample, subject

CSV_PATH = Path(__file__).resolve().parent / "data" / "cell-count.csv"


def _condition_name(value: str) -> str | None:
    # "healthy" means no diagnosed condition, not a condition named "healthy".
    return None if value == "healthy" else value


def _treatment_name(value: str) -> str | None:
    # "none" means no treatment given, not a treatment named "none".
    return None if value == "none" else value


def load_data(csv_path: Path) -> None:
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))

    with engine.begin() as conn:
        conn.execute(delete(sample))
        conn.execute(delete(subject))
        conn.execute(delete(project))

        project_ids: dict[str, int] = {}
        subject_ids: dict[str, int] = {}

        for row in rows:
            project_source_id = row["project"]
            if project_source_id not in project_ids:
                result = conn.execute(
                    insert(project).values(
                        source_id=project_source_id,
                        sample_type=row["sample_type"],
                    )
                )
                project_ids[project_source_id] = result.inserted_primary_key[0]

            subject_source_id = row["subject"]
            if subject_source_id not in subject_ids:
                result = conn.execute(
                    insert(subject).values(
                        source_id=subject_source_id,
                        project_id=project_ids[project_source_id],
                        age=int(row["age"]),
                        sex=row["sex"],
                        treatment_response=row["response"] or None,
                        condition_name=_condition_name(row["condition"]),
                        treatment_name=_treatment_name(row["treatment"]),
                    )
                )
                subject_ids[subject_source_id] = result.inserted_primary_key[0]

            conn.execute(
                insert(sample).values(
                    source_id=row["sample"],
                    subject_id=subject_ids[subject_source_id],
                    time_from_treatment=int(row["time_from_treatment_start"]),
                    b_cell=int(row["b_cell"]),
                    cd8_t_cell=int(row["cd8_t_cell"]),
                    cd4_t_cell=int(row["cd4_t_cell"]),
                    nk_cell=int(row["nk_cell"]),
                    monocyte=int(row["monocyte"]),
                )
            )

    print(
        f"Loaded {len(project_ids)} projects, {len(subject_ids)} subjects, "
        f"{len(rows)} samples."
    )


def main() -> None:
    init_db()
    load_data(CSV_PATH)


if __name__ == "__main__":
    main()
