"""Tests for backend.crunching.samples.

get_samples pulls Sample rows joined with Subject and Project, filtered by
condition/treatment/sample_type/time_from_treatment; get_field_values pulls
distinct raw values (including None) for those same filterable fields.
Sorting/grouping is previsualizing's job -- see test_samples_previsualizing.py
-- these tests only cover filtering and the joined detail shape.
"""

import pytest

from backend.crunching.samples import get_field_values, get_samples
from tests.conftest import insert_project, insert_sample, insert_subject

COUNTS = {"b_cell": 10, "cd8_t_cell": 20, "cd4_t_cell": 30, "nk_cell": 25, "monocyte": 15}


def test_no_samples_returns_empty_list(engine):
    with engine.connect() as conn:
        result = get_samples(
            conn, condition=None, treatment=None, sample_type=None, time_from_treatment=None
        )
    assert result == []


def test_no_filters_returns_full_joined_detail(engine):
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

    with engine.connect() as conn:
        [detail] = get_samples(
            conn, condition=None, treatment=None, sample_type=None, time_from_treatment=None
        )

    assert detail.project_source_id == "prj1"
    assert detail.subject_source_id == "sbj1"
    assert detail.condition == "melanoma"
    assert detail.treatment == "miraclib"
    assert detail.age == 42
    assert detail.sex == "F"
    assert detail.response == "yes"
    assert detail.sample_type == "PBMC"
    assert detail.time_from_treatment == 7
    assert detail.b_cell == 10
    assert detail.cd8_t_cell == 20
    assert detail.cd4_t_cell == 30
    assert detail.nk_cell == 25
    assert detail.monocyte == 15


def test_filters_by_condition_treatment_sample_type_and_time(engine):
    project_id = insert_project(engine, sample_type="PBMC")
    other_project_id = insert_project(engine, source_id="prj2", sample_type="WB")

    matching = insert_subject(
        engine, project_id, source_id="match", condition_name="melanoma", treatment_name="miraclib"
    )
    wrong_condition = insert_subject(
        engine, project_id, source_id="wrong-cond", condition_name="carcinoma", treatment_name="miraclib"
    )
    wrong_treatment = insert_subject(
        engine, project_id, source_id="wrong-treat", condition_name="melanoma", treatment_name="phauximab"
    )
    wrong_sample_type = insert_subject(
        engine, other_project_id, source_id="wrong-type", condition_name="melanoma", treatment_name="miraclib"
    )

    insert_sample(engine, matching, "s-match", COUNTS, time_from_treatment=7)
    insert_sample(engine, matching, "s-wrong-time", COUNTS, time_from_treatment=14)
    insert_sample(engine, wrong_condition, "s-wrong-cond", COUNTS, time_from_treatment=7)
    insert_sample(engine, wrong_treatment, "s-wrong-treat", COUNTS, time_from_treatment=7)
    insert_sample(engine, wrong_sample_type, "s-wrong-type", COUNTS, time_from_treatment=7)

    with engine.connect() as conn:
        result = get_samples(
            conn,
            condition="melanoma",
            treatment="miraclib",
            sample_type="PBMC",
            time_from_treatment=7,
        )

    assert [d.subject_source_id for d in result] == ["match"]


def test_empty_string_condition_and_treatment_filter_to_null_not_literal_empty(engine):
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

    with engine.connect() as conn:
        by_condition = get_samples(
            conn, condition="", treatment=None, sample_type=None, time_from_treatment=None
        )
        by_treatment = get_samples(
            conn, condition=None, treatment="", sample_type=None, time_from_treatment=None
        )

    assert [d.subject_source_id for d in by_condition] == ["untreated"]
    assert [d.subject_source_id for d in by_treatment] == ["untreated"]


def test_get_field_values_includes_none_for_condition_and_treatment(engine):
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
    # get_field_values selects through a Sample join, so both subjects need
    # a sample row to be visible at all.
    insert_sample(engine, untreated, "s-untreated", COUNTS)
    insert_sample(engine, treated, "s-treated", COUNTS)

    with engine.connect() as conn:
        conditions = get_field_values(conn, field="condition")
        treatments = get_field_values(conn, field="treatment")

    assert set(conditions) == {"melanoma", None}
    assert set(treatments) == {"miraclib", None}


def test_get_field_values_for_sample_type_and_time_never_include_none(engine):
    project_id = insert_project(engine, sample_type="PBMC")
    subject_id = insert_subject(engine, project_id)
    insert_sample(engine, subject_id, "s1", COUNTS, time_from_treatment=7)

    with engine.connect() as conn:
        sample_types = get_field_values(conn, field="sample_type")
        times = get_field_values(conn, field="time_from_treatment")

    assert sample_types == ["PBMC"]
    assert times == [7]


def test_get_field_values_returns_distinct_values_only(engine):
    project_id = insert_project(engine)
    subject_a = insert_subject(engine, project_id, source_id="a", condition_name="melanoma")
    subject_b = insert_subject(engine, project_id, source_id="b", condition_name="melanoma")
    insert_sample(engine, subject_a, "s-a", COUNTS)
    insert_sample(engine, subject_b, "s-b", COUNTS)

    with engine.connect() as conn:
        conditions = get_field_values(conn, field="condition")

    assert conditions == ["melanoma"]
