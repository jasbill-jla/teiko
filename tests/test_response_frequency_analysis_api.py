"""Integration tests for GET /api/response-frequency-analysis.

Goes through the real route -> previsualizing -> crunching stack, including
the actual Mann-Whitney U significance method (not a stub) -- unlike
test_response_significance.py, which tests that composition in isolation
from any particular statistical test.
"""

from backend.crunching.cell_frequencies import POPULATIONS
from backend.crunching.mann_whitney_significance import BONFERRONI_ALPHA
from tests.conftest import insert_project, insert_sample, insert_subject


def test_no_matching_data_returns_empty_boxplots(client):
    response = client.get(
        "/api/response-frequency-analysis",
        params={"condition": "melanoma", "treatment": "miraclib", "sample_type": "PBMC"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["boxplots"] == []
    assert isinstance(data["methodology"], str) and data["methodology"]


def test_missing_required_query_param_is_rejected(client):
    response = client.get(
        "/api/response-frequency-analysis",
        params={"condition": "melanoma", "treatment": "miraclib"},  # sample_type missing
    )
    assert response.status_code == 422


def test_median_threshold_query_param_no_longer_accepted_but_silently_ignored(client, engine):
    # median_threshold was dropped from the endpoint's parameters -- FastAPI
    # ignores unrecognized query params rather than rejecting them, so a
    # stale client still passing it should get a normal response, not a 422.
    response = client.get(
        "/api/response-frequency-analysis",
        params={
            "condition": "melanoma",
            "treatment": "miraclib",
            "sample_type": "PBMC",
            "median_threshold": "10",
        },
    )
    assert response.status_code == 200


def _insert_responder_and_non_responder(engine, condition, treatment, sample_type, counts_yes, counts_no):
    project_id = insert_project(engine, sample_type=sample_type)
    responder = insert_subject(
        engine,
        project_id,
        source_id="r",
        condition_name=condition,
        treatment_name=treatment,
        treatment_response="yes",
    )
    non_responder = insert_subject(
        engine,
        project_id,
        source_id="nr",
        condition_name=condition,
        treatment_name=treatment,
        treatment_response="no",
    )
    insert_sample(engine, responder, "s-r", counts_yes)
    insert_sample(engine, non_responder, "s-nr", counts_no)


def test_returns_all_five_populations_unconditionally(client, engine):
    counts = {"b_cell": 10, "cd8_t_cell": 20, "cd4_t_cell": 30, "nk_cell": 25, "monocyte": 15}
    _insert_responder_and_non_responder(
        engine, "melanoma", "miraclib", "PBMC", counts, counts
    )

    data = client.get(
        "/api/response-frequency-analysis",
        params={"condition": "melanoma", "treatment": "miraclib", "sample_type": "PBMC"},
    ).json()

    assert len(data["boxplots"]) == 5
    assert {b["population"] for b in data["boxplots"]} == set(POPULATIONS)
    # Identical data for both groups -- nothing should reach significance.
    assert all(b["significant"] is False for b in data["boxplots"])


def test_boxplot_shape_and_values_for_one_population(client, engine):
    counts_yes = {"b_cell": 10, "cd8_t_cell": 20, "cd4_t_cell": 30, "nk_cell": 25, "monocyte": 15}
    counts_no = {"b_cell": 50, "cd8_t_cell": 20, "cd4_t_cell": 10, "nk_cell": 10, "monocyte": 10}
    _insert_responder_and_non_responder(
        engine, "melanoma", "miraclib", "PBMC", counts_yes, counts_no
    )

    data = client.get(
        "/api/response-frequency-analysis",
        params={"condition": "melanoma", "treatment": "miraclib", "sample_type": "PBMC"},
    ).json()

    [b_cell] = [b for b in data["boxplots"] if b["population"] == "b_cell"]
    assert set(b_cell.keys()) == {
        "population",
        "responder",
        "non_responder",
        "statistic",
        "significant",
    }
    assert set(b_cell["responder"].keys()) == {"minimum", "q1", "median", "q3", "maximum"}

    total_yes = sum(counts_yes.values())
    total_no = sum(counts_no.values())
    assert b_cell["responder"]["median"] == 100 * counts_yes["b_cell"] / total_yes
    assert b_cell["non_responder"]["median"] == 100 * counts_no["b_cell"] / total_no
    assert 0.0 <= b_cell["statistic"] <= 1.0
    assert b_cell["significant"] == (b_cell["statistic"] < BONFERRONI_ALPHA)


def test_clearly_separated_population_is_flagged_significant(client, engine):
    project_id = insert_project(engine, sample_type="PBMC")
    for i in range(10):
        responder = insert_subject(
            engine, project_id, source_id=f"r{i}", treatment_response="yes"
        )
        insert_sample(
            engine,
            responder,
            f"s-r{i}",
            {"b_cell": 60 + i, "cd8_t_cell": 10, "cd4_t_cell": 10, "nk_cell": 10, "monocyte": 10},
        )
        non_responder = insert_subject(
            engine, project_id, source_id=f"nr{i}", treatment_response="no"
        )
        insert_sample(
            engine,
            non_responder,
            f"s-nr{i}",
            {"b_cell": 5 + i, "cd8_t_cell": 10, "cd4_t_cell": 10, "nk_cell": 10, "monocyte": 10},
        )

    data = client.get(
        "/api/response-frequency-analysis",
        params={"condition": "melanoma", "treatment": "miraclib", "sample_type": "PBMC"},
    ).json()

    assert len(data["boxplots"]) == 5
    [b_cell] = [b for b in data["boxplots"] if b["population"] == "b_cell"]
    assert b_cell["significant"] is True
    assert b_cell["statistic"] < BONFERRONI_ALPHA
    assert "Mann-Whitney U" in data["methodology"]
