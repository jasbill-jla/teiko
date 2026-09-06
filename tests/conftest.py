"""Shared fixtures/helpers for backend tests: a scratch SQLite DB per test.

Schema is created with metadata.create_all(), not Alembic migrations --
these tests are about function/endpoint behavior against a known schema, not
about verifying migrations (see backend/alembic for that).
"""

import pytest
from sqlalchemy import Engine, insert, create_engine

from backend.models.tables import metadata, project, sample, subject


@pytest.fixture
def engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    metadata.create_all(eng)
    yield eng
    eng.dispose()


def insert_project(engine: Engine, source_id: str = "prj1", sample_type: str = "PBMC") -> int:
    with engine.begin() as conn:
        return conn.execute(
            insert(project).values(source_id=source_id, sample_type=sample_type)
        ).inserted_primary_key[0]


def insert_subject(
    engine: Engine,
    project_id: int,
    source_id: str = "sbj000",
    condition_name: str | None = "melanoma",
    treatment_name: str | None = "miraclib",
    treatment_response: str | None = "yes",
    age: int = 57,
    sex: str = "M",
) -> int:
    with engine.begin() as conn:
        return conn.execute(
            insert(subject).values(
                source_id=source_id,
                project_id=project_id,
                age=age,
                sex=sex,
                treatment_response=treatment_response,
                condition_name=condition_name,
                treatment_name=treatment_name,
            )
        ).inserted_primary_key[0]


def insert_sample(
    engine: Engine,
    subject_id: int,
    source_id: str,
    counts: dict[str, int],
    time_from_treatment: int = 0,
) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(sample).values(
                source_id=source_id,
                subject_id=subject_id,
                time_from_treatment=time_from_treatment,
                **counts,
            )
        )
