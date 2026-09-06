"""Integration tests for GET /api/cell-frequencies.

Schema is created with metadata.create_all(), not Alembic migrations --
these tests are about the endpoint's behavior against a known schema, not
about verifying migrations (see backend/alembic for that).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, insert

from backend.core.db import get_connection
from backend.main import app
from backend.models.tables import metadata, project, sample, subject

POPULATIONS = ("b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte")


@pytest.fixture
def engine(tmp_path):
    eng = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def client(engine):
    def override_get_connection():
        with engine.connect() as conn:
            yield conn

    app.dependency_overrides[get_connection] = override_get_connection
    yield TestClient(app)
    app.dependency_overrides.clear()


def _insert_subject(engine, source_id="sbj000"):
    with engine.begin() as conn:
        project_id = conn.execute(
            insert(project).values(source_id="prj1", sample_type="PBMC")
        ).inserted_primary_key[0]
        return conn.execute(
            insert(subject).values(
                source_id=source_id,
                project_id=project_id,
                age=57,
                sex="M",
                treatment_response="yes",
                condition_name="melanoma",
                treatment_name="miraclib",
            )
        ).inserted_primary_key[0]


def _insert_sample(engine, subject_id, source_id, counts):
    with engine.begin() as conn:
        conn.execute(
            insert(sample).values(
                source_id=source_id,
                subject_id=subject_id,
                time_from_treatment=0,
                **counts,
            )
        )


def test_no_samples_returns_empty_list(client):
    response = client.get("/api/cell-frequencies")
    assert response.status_code == 200
    assert response.json() == []


def test_one_sample_returns_5_rows_with_correct_values(engine, client):
    subject_id = _insert_subject(engine)
    counts = {
        "b_cell": 10,
        "cd8_t_cell": 20,
        "cd4_t_cell": 30,
        "nk_cell": 25,
        "monocyte": 15,
    }
    _insert_sample(engine, subject_id, "sample00000", counts)

    response = client.get("/api/cell-frequencies")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 5
    assert set(data[0].keys()) == {
        "sample",
        "population",
        "count",
        "total_count",
        "percentage",
    }
    assert {row["population"] for row in data} == set(POPULATIONS)

    total = sum(counts.values())
    by_population = {row["population"]: row for row in data}
    for population, count in counts.items():
        row = by_population[population]
        assert row["sample"] == "sample00000"
        assert row["count"] == count
        assert row["total_count"] == total
        assert row["percentage"] == pytest.approx(100 * count / total)

    assert sum(row["percentage"] for row in data) == pytest.approx(100.0)


def test_multiple_samples_are_independent_and_ordered(engine, client):
    subject_id = _insert_subject(engine)
    _insert_sample(
        engine,
        subject_id,
        "sampleA",
        {"b_cell": 1, "cd8_t_cell": 1, "cd4_t_cell": 1, "nk_cell": 1, "monocyte": 1},
    )
    _insert_sample(
        engine,
        subject_id,
        "sampleB",
        {"b_cell": 10, "cd8_t_cell": 0, "cd4_t_cell": 0, "nk_cell": 0, "monocyte": 0},
    )

    data = client.get("/api/cell-frequencies").json()
    assert len(data) == 10

    # Rows come back grouped by sample (insertion order), each in fixed population order.
    assert [row["sample"] for row in data[:5]] == ["sampleA"] * 5
    assert [row["population"] for row in data[:5]] == list(POPULATIONS)
    assert [row["sample"] for row in data[5:]] == ["sampleB"] * 5

    assert all(row["total_count"] == 5 for row in data[:5])
    assert all(row["percentage"] == pytest.approx(20.0) for row in data[:5])

    b_cell_b = next(row for row in data[5:] if row["population"] == "b_cell")
    assert b_cell_b["total_count"] == 10
    assert b_cell_b["percentage"] == pytest.approx(100.0)


def test_samples_ordered_by_insertion_not_by_source_id(engine, client):
    # source_id sorts the opposite of insertion order here, so this proves
    # the endpoint orders by Sample.id (insertion order) and not by the
    # source_id string -- test_multiple_samples_are_independent_and_ordered
    # alone can't tell those two apart, since there source_id happens to
    # already be in insertion order.
    subject_id = _insert_subject(engine)
    counts = {"b_cell": 1, "cd8_t_cell": 1, "cd4_t_cell": 1, "nk_cell": 1, "monocyte": 1}
    _insert_sample(engine, subject_id, "zzz_inserted_first", counts)
    _insert_sample(engine, subject_id, "aaa_inserted_second", counts)

    data = client.get("/api/cell-frequencies").json()
    assert len(data) == 10

    assert [row["sample"] for row in data[:5]] == ["zzz_inserted_first"] * 5
    assert [row["population"] for row in data[:5]] == list(POPULATIONS)
    assert [row["sample"] for row in data[5:]] == ["aaa_inserted_second"] * 5
    assert [row["population"] for row in data[5:]] == list(POPULATIONS)
