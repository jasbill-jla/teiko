"""Tests for backend.previsualizing.samples.

get_samples_result sorts, and optionally groups+counts,
crunching.samples.get_samples's output; get_field_values sorts and
stringifies crunching.samples.get_field_values's output for the samples
page's filter dropdowns. Filtering itself is crunching's job -- see
test_samples_crunching.py -- so these tests focus on sort order, grouping,
and count semantics.
"""

from backend.previsualizing.samples import get_field_values, get_samples_result
from backend.schemas.samples import GroupCount
from tests.conftest import insert_project, insert_sample, insert_subject

COUNTS = {"b_cell": 10, "cd8_t_cell": 20, "cd4_t_cell": 30, "nk_cell": 25, "monocyte": 15}


def _query(conn, **overrides):
    params = dict(
        condition=None,
        treatment=None,
        sample_type=None,
        time_from_treatment=None,
        grouping=None,
        group_count_field=None,
    )
    params.update(overrides)
    return get_samples_result(conn, **params)


def test_filters_pass_through_to_crunching(engine):
    project_id = insert_project(engine, sample_type="PBMC")
    other_project = insert_project(engine, source_id="prj2", sample_type="WB")
    matching = insert_subject(
        engine, project_id, source_id="match", condition_name="melanoma", treatment_name="miraclib"
    )
    other = insert_subject(
        engine, other_project, source_id="other", condition_name="melanoma", treatment_name="miraclib"
    )
    insert_sample(engine, matching, "s-match", COUNTS)
    insert_sample(engine, other, "s-other", COUNTS)

    with engine.connect() as conn:
        result = _query(conn, condition="melanoma", treatment="miraclib", sample_type="PBMC")

    assert [s.subject_source_id for s in result.samples] == ["match"]


def test_no_grouping_sorts_by_project_then_subject_and_has_no_counts(engine):
    project_a = insert_project(engine, source_id="prj-a")
    project_b = insert_project(engine, source_id="prj-b")
    subject_a2 = insert_subject(engine, project_a, source_id="a2")
    subject_a1 = insert_subject(engine, project_a, source_id="a1")
    subject_b1 = insert_subject(engine, project_b, source_id="b1")
    insert_sample(engine, subject_a2, "s-a2", COUNTS)
    insert_sample(engine, subject_a1, "s-a1", COUNTS)
    insert_sample(engine, subject_b1, "s-b1", COUNTS)

    with engine.connect() as conn:
        result = _query(conn)

    assert [(s.project_source_id, s.subject_source_id) for s in result.samples] == [
        ("prj-a", "a1"),
        ("prj-a", "a2"),
        ("prj-b", "b1"),
    ]
    assert result.counts == []


def test_grouping_by_project_counts_samples_not_subjects(engine):
    project_id = insert_project(engine, source_id="prj1")
    subject_id = insert_subject(engine, project_id)
    insert_sample(engine, subject_id, "s1", COUNTS)
    insert_sample(engine, subject_id, "s2", COUNTS)  # same subject, 2 samples

    with engine.connect() as conn:
        result = _query(conn, grouping="project")

    assert result.counts == [GroupCount(group="prj1", count=2)]


def test_grouping_by_subject_sex_counts_distinct_subjects_not_samples(engine):
    project_id = insert_project(engine)
    subject_id = insert_subject(engine, project_id, sex="F")
    insert_sample(engine, subject_id, "s1", COUNTS)
    insert_sample(engine, subject_id, "s2", COUNTS)  # same subject, same sex

    with engine.connect() as conn:
        result = _query(conn, grouping="subject", group_count_field="sex")

    assert result.counts == [GroupCount(group="F", count=1)]


def test_grouping_by_subject_response_uses_none_sentinel_for_no_response(engine):
    project_id = insert_project(engine)
    untreated = insert_subject(
        engine,
        project_id,
        source_id="untreated",
        condition_name=None,
        treatment_name=None,
        treatment_response=None,
    )
    insert_sample(engine, untreated, "s1", COUNTS)

    with engine.connect() as conn:
        result = _query(conn, grouping="subject", group_count_field="response")

    assert result.counts == [GroupCount(group="none", count=1)]
    # The sample record itself still carries the real null, not the sentinel.
    assert result.samples[0].response is None


def test_grouping_by_subject_sorts_by_group_then_subject(engine):
    project_id = insert_project(engine)
    male = insert_subject(engine, project_id, source_id="m1", sex="M")
    female = insert_subject(engine, project_id, source_id="f1", sex="F")
    insert_sample(engine, male, "s-m", COUNTS)
    insert_sample(engine, female, "s-f", COUNTS)

    with engine.connect() as conn:
        result = _query(conn, grouping="subject", group_count_field="sex")

    assert [(s.sex, s.subject_source_id) for s in result.samples] == [("F", "f1"), ("M", "m1")]


def test_get_field_values_sorts_none_first_and_stringifies_it_as_empty(engine):
    project_id = insert_project(engine)
    no_condition = insert_subject(
        engine,
        project_id,
        source_id="none-cond",
        condition_name=None,
        treatment_name=None,
        treatment_response=None,
    )
    zebra = insert_subject(engine, project_id, source_id="zeb", condition_name="zebra-syndrome")
    apple = insert_subject(engine, project_id, source_id="app", condition_name="apple-itis")
    insert_sample(engine, no_condition, "s1", COUNTS)
    insert_sample(engine, zebra, "s2", COUNTS)
    insert_sample(engine, apple, "s3", COUNTS)

    with engine.connect() as conn:
        values = get_field_values(conn, field="condition")

    assert values == ["", "apple-itis", "zebra-syndrome"]


def test_get_field_values_for_time_from_treatment_stringifies_ints(engine):
    project_id = insert_project(engine)
    subject_id = insert_subject(engine, project_id)
    insert_sample(engine, subject_id, "s1", COUNTS, time_from_treatment=14)
    insert_sample(engine, subject_id, "s2", COUNTS, time_from_treatment=7)

    with engine.connect() as conn:
        values = get_field_values(conn, field="time_from_treatment")

    assert values == ["7", "14"]
