"""Tests for backend.crunching.response_frequencies.

get_response_frequencies (per-sample) and get_response_subject_frequencies
(per-subject) share the same filtering/scoping logic but differ in exactly
one respect -- whether a subject's multiple samples collapse to one value --
so most tests below exercise both to pin that difference precisely.
"""

import pytest

from backend.crunching.response_frequencies import (
    get_response_frequencies,
    get_response_subject_frequencies,
)
from tests.conftest import insert_project, insert_sample, insert_subject

COUNTS = {"b_cell": 10, "cd8_t_cell": 20, "cd4_t_cell": 30, "nk_cell": 25, "monocyte": 15}


def test_no_matching_data_returns_empty_dicts(engine):
    with engine.connect() as conn:
        frequencies = get_response_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )
        subject_frequencies = get_response_subject_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    assert frequencies == {population: {} for population in COUNTS}
    assert subject_frequencies == {population: {} for population in COUNTS}


def test_filters_by_condition_treatment_and_sample_type(engine):
    project_id = insert_project(engine, sample_type="PBMC")
    other_project_id = insert_project(engine, source_id="prj2", sample_type="WB")

    matching = insert_subject(
        engine, project_id, source_id="match", condition_name="melanoma", treatment_name="miraclib"
    )
    wrong_condition = insert_subject(
        engine,
        project_id,
        source_id="wrong-condition",
        condition_name="carcinoma",
        treatment_name="miraclib",
    )
    wrong_treatment = insert_subject(
        engine,
        project_id,
        source_id="wrong-treatment",
        condition_name="melanoma",
        treatment_name="phauximab",
    )
    wrong_sample_type = insert_subject(
        engine,
        other_project_id,
        source_id="wrong-sample-type",
        condition_name="melanoma",
        treatment_name="miraclib",
    )

    insert_sample(engine, matching, "s-match", COUNTS)
    insert_sample(engine, wrong_condition, "s-wrong-condition", COUNTS)
    insert_sample(engine, wrong_treatment, "s-wrong-treatment", COUNTS)
    insert_sample(engine, wrong_sample_type, "s-wrong-sample-type", COUNTS)

    with engine.connect() as conn:
        frequencies = get_response_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    assert frequencies["b_cell"]["yes"] == [pytest.approx(10.0)]


def test_excludes_subjects_with_no_response(engine):
    project_id = insert_project(engine)
    untreated = insert_subject(
        engine,
        project_id,
        condition_name=None,
        treatment_name=None,
        treatment_response=None,
    )
    insert_sample(engine, untreated, "s1", COUNTS)

    with engine.connect() as conn:
        frequencies = get_response_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )
        subject_frequencies = get_response_subject_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    assert frequencies["b_cell"] == {}
    assert subject_frequencies["b_cell"] == {}


def test_per_sample_frequencies_computed_correctly(engine):
    project_id = insert_project(engine)
    subject_id = insert_subject(engine, project_id, treatment_response="yes")
    insert_sample(engine, subject_id, "s1", COUNTS)

    with engine.connect() as conn:
        frequencies = get_response_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    total = sum(COUNTS.values())
    for population, count in COUNTS.items():
        assert frequencies[population]["yes"] == [pytest.approx(100 * count / total)]


def test_per_sample_frequencies_one_value_per_sample_not_per_subject(engine):
    project_id = insert_project(engine)
    subject_id = insert_subject(engine, project_id, treatment_response="yes")
    insert_sample(engine, subject_id, "s1", COUNTS)
    insert_sample(
        engine,
        subject_id,
        "s2",
        {"b_cell": 90, "cd8_t_cell": 10, "cd4_t_cell": 0, "nk_cell": 0, "monocyte": 0},
    )

    with engine.connect() as conn:
        frequencies = get_response_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    # Two samples from the same subject -> two separate entries.
    assert len(frequencies["b_cell"]["yes"]) == 2
    assert sorted(frequencies["b_cell"]["yes"]) == [
        pytest.approx(10.0),
        pytest.approx(90.0),
    ]


def test_subject_frequencies_collapse_multiple_samples_to_their_median(engine):
    project_id = insert_project(engine)
    subject_id = insert_subject(engine, project_id, treatment_response="yes")
    # Three b_cell percentages for the same subject: 10%, 50%, 90% -- median 50%.
    insert_sample(
        engine, subject_id, "s1", {"b_cell": 10, "cd8_t_cell": 90, "cd4_t_cell": 0, "nk_cell": 0, "monocyte": 0}
    )
    insert_sample(
        engine, subject_id, "s2", {"b_cell": 50, "cd8_t_cell": 50, "cd4_t_cell": 0, "nk_cell": 0, "monocyte": 0}
    )
    insert_sample(
        engine, subject_id, "s3", {"b_cell": 90, "cd8_t_cell": 10, "cd4_t_cell": 0, "nk_cell": 0, "monocyte": 0}
    )

    with engine.connect() as conn:
        subject_frequencies = get_response_subject_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    # One subject, three samples -> exactly one (median) value, not three.
    assert subject_frequencies["b_cell"]["yes"] == [pytest.approx(50.0)]


def test_subject_frequencies_one_value_per_subject_across_multiple_subjects(engine):
    project_id = insert_project(engine)
    subject_a = insert_subject(engine, project_id, source_id="a", treatment_response="yes")
    subject_b = insert_subject(engine, project_id, source_id="b", treatment_response="yes")
    insert_sample(engine, subject_a, "s1", COUNTS)
    insert_sample(engine, subject_b, "s2", COUNTS)

    with engine.connect() as conn:
        subject_frequencies = get_response_subject_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    assert len(subject_frequencies["b_cell"]["yes"]) == 2


def test_responders_and_non_responders_kept_separate(engine):
    project_id = insert_project(engine)
    responder = insert_subject(engine, project_id, source_id="r", treatment_response="yes")
    non_responder = insert_subject(engine, project_id, source_id="nr", treatment_response="no")
    insert_sample(engine, responder, "s1", COUNTS)
    insert_sample(
        engine,
        non_responder,
        "s2",
        {"b_cell": 50, "cd8_t_cell": 20, "cd4_t_cell": 10, "nk_cell": 10, "monocyte": 10},
    )

    with engine.connect() as conn:
        frequencies = get_response_frequencies(
            conn, condition="melanoma", treatment="miraclib", sample_type="PBMC"
        )

    assert frequencies["b_cell"]["yes"] == [pytest.approx(10.0)]
    assert frequencies["b_cell"]["no"] == [pytest.approx(50.0)]
