"""Integration tests for GET /api/samples and GET /api/samples/field-values.

Schema is created with metadata.create_all(), not Alembic migrations -- see
tests/conftest.py. Filtering/sorting/grouping semantics are covered in
test_samples_crunching.py and test_samples_previsualizing.py; these tests
check that the endpoint wires query params through and shapes its response
correctly.
"""

from tests.conftest import insert_project, insert_sample, insert_subject

COUNTS = {"b_cell": 10, "cd8_t_cell": 20, "cd4_t_cell": 30, "nk_cell": 25, "monocyte": 15}


def test_no_samples_returns_empty_result(client):
    response = client.get("/api/samples")
    assert response.status_code == 200
    assert response.json() == {"samples": [], "counts": []}


def test_returns_full_sample_record_shape(engine, client):
    project_id = insert_project(engine, source_id="prj1", sample_type="PBMC")
    subject_id = insert_subject(
        engine,
        project_id,
        source_id="sbj1",
        condition_name="melanoma",
        treatment_name="miraclib",
        treatment_response="yes",
        age=42,
        sex="F",
    )
    insert_sample(engine, subject_id, "s1", COUNTS, time_from_treatment=7)

    data = client.get("/api/samples").json()

    assert data["counts"] == []
    [record] = data["samples"]
    assert record == {
        "project_source_id": "prj1",
        "condition": "melanoma",
        "treatment": "miraclib",
        "subject_source_id": "sbj1",
        "age": 42,
        "sex": "F",
        "response": "yes",
        "sample_type": "PBMC",
        "time_from_treatment": 7,
        **COUNTS,
    }


def test_filters_by_condition_treatment_sample_type_and_time(engine, client):
    project_id = insert_project(engine, sample_type="PBMC")
    matching = insert_subject(engine, project_id, source_id="match")
    other = insert_subject(engine, project_id, source_id="other", condition_name="carcinoma")
    insert_sample(engine, matching, "s-match", COUNTS, time_from_treatment=7)
    insert_sample(engine, matching, "s-wrong-time", COUNTS, time_from_treatment=14)
    insert_sample(engine, other, "s-other", COUNTS, time_from_treatment=7)

    response = client.get(
        "/api/samples",
        params={
            "condition": "melanoma",
            "treatment": "miraclib",
            "sample_type": "PBMC",
            "time_from_treatment": 7,
        },
    )
    data = response.json()

    assert [s["subject_source_id"] for s in data["samples"]] == ["match"]


def test_empty_string_condition_filters_to_no_value_recorded(engine, client):
    project_id = insert_project(engine)
    untreated = insert_subject(
        engine,
        project_id,
        source_id="untreated",
        condition_name=None,
        treatment_name=None,
        treatment_response=None,
    )
    treated = insert_subject(engine, project_id, source_id="treated")
    insert_sample(engine, untreated, "s-untreated", COUNTS)
    insert_sample(engine, treated, "s-treated", COUNTS)

    data = client.get("/api/samples", params={"condition": ""}).json()

    assert [s["subject_source_id"] for s in data["samples"]] == ["untreated"]


def test_grouping_by_project_returns_sample_counts(engine, client):
    project_id = insert_project(engine, source_id="prj1")
    subject_id = insert_subject(engine, project_id)
    insert_sample(engine, subject_id, "s1", COUNTS)
    insert_sample(engine, subject_id, "s2", COUNTS)

    data = client.get("/api/samples", params={"grouping": "project"}).json()

    assert data["counts"] == [{"group": "prj1", "count": 2}]


def test_grouping_by_subject_with_sex_returns_distinct_subject_counts(engine, client):
    project_id = insert_project(engine)
    subject_id = insert_subject(engine, project_id, sex="F")
    insert_sample(engine, subject_id, "s1", COUNTS)
    insert_sample(engine, subject_id, "s2", COUNTS)

    data = client.get(
        "/api/samples", params={"grouping": "subject", "group_count_field": "sex"}
    ).json()

    assert data["counts"] == [{"group": "F", "count": 1}]


def test_grouping_by_subject_without_group_count_field_returns_422(client):
    response = client.get("/api/samples", params={"grouping": "subject"})

    assert response.status_code == 422
    assert "group_count_field" in response.json()["detail"]


def test_field_values_condition_includes_empty_string_for_none(engine, client):
    project_id = insert_project(engine)
    no_condition = insert_subject(
        engine,
        project_id,
        source_id="none-cond",
        condition_name=None,
        treatment_name=None,
        treatment_response=None,
    )
    treated = insert_subject(engine, project_id, source_id="treated")
    insert_sample(engine, no_condition, "s1", COUNTS)
    insert_sample(engine, treated, "s2", COUNTS)

    data = client.get("/api/samples/field-values", params={"field": "condition"}).json()

    assert data == ["", "melanoma"]


def test_field_values_sample_type(engine, client):
    project_id = insert_project(engine, sample_type="PBMC")
    subject_id = insert_subject(engine, project_id)
    insert_sample(engine, subject_id, "s1", COUNTS)

    data = client.get("/api/samples/field-values", params={"field": "sample_type"}).json()

    assert data == ["PBMC"]


def test_field_values_rejects_unknown_field(client):
    response = client.get("/api/samples/field-values", params={"field": "bogus"})

    assert response.status_code == 422
