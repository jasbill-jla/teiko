"""Tests for backend.crunching.response_significance.

get_response_significance_analysis composes get_response_frequencies,
get_response_subject_frequencies, compute_boxplot_stats, and a
SignificanceMethod -- these tests check the composition/wiring, not the
statistics themselves (see test_mann_whitney_significance.py for that).
"""

import pytest

from backend.crunching.cell_frequencies import POPULATIONS
from backend.crunching.response_significance import get_response_significance_analysis
from backend.crunching.significance import SignificanceMethod, SignificanceResult
from tests.conftest import insert_project, insert_sample, insert_subject

COUNTS = {"b_cell": 10, "cd8_t_cell": 20, "cd4_t_cell": 30, "nk_cell": 25, "monocyte": 15}

# A stand-in SignificanceMethod so these tests don't depend on Mann-Whitney
# U's actual statistical behavior -- just whether get_response_significance_analysis
# calls it correctly and assembles the result correctly.
ALWAYS_SIGNIFICANT = SignificanceMethod(
    name="stub",
    description="stub",
    test=lambda a, b: SignificanceResult(statistic=0.0, significant=True),
)
NEVER_SIGNIFICANT = SignificanceMethod(
    name="stub",
    description="stub",
    test=lambda a, b: SignificanceResult(statistic=1.0, significant=False),
)


def _setup_both_response_groups(engine):
    project_id = insert_project(engine)
    responder = insert_subject(engine, project_id, source_id="r", treatment_response="yes")
    non_responder = insert_subject(engine, project_id, source_id="nr", treatment_response="no")
    insert_sample(engine, responder, "s-r", COUNTS)
    insert_sample(engine, non_responder, "s-nr", COUNTS)


def test_no_matching_data_returns_empty_list(engine):
    with engine.connect() as conn:
        result = get_response_significance_analysis(
            conn,
            condition="melanoma",
            treatment="miraclib",
            sample_type="PBMC",
            method=ALWAYS_SIGNIFICANT,
        )
    assert result == []


def test_missing_one_response_group_excludes_all_populations(engine):
    project_id = insert_project(engine)
    responder_only = insert_subject(engine, project_id, treatment_response="yes")
    insert_sample(engine, responder_only, "s1", COUNTS)

    with engine.connect() as conn:
        result = get_response_significance_analysis(
            conn,
            condition="melanoma",
            treatment="miraclib",
            sample_type="PBMC",
            method=ALWAYS_SIGNIFICANT,
        )

    assert result == []


def test_returns_all_populations_in_fixed_order_when_both_groups_present(engine):
    _setup_both_response_groups(engine)

    with engine.connect() as conn:
        result = get_response_significance_analysis(
            conn,
            condition="melanoma",
            treatment="miraclib",
            sample_type="PBMC",
            method=ALWAYS_SIGNIFICANT,
        )

    assert [analysis.population for analysis in result] == list(POPULATIONS)


def test_significant_flag_and_statistic_come_from_the_given_method(engine):
    _setup_both_response_groups(engine)

    with engine.connect() as conn:
        significant_result = get_response_significance_analysis(
            conn,
            condition="melanoma",
            treatment="miraclib",
            sample_type="PBMC",
            method=ALWAYS_SIGNIFICANT,
        )
        not_significant_result = get_response_significance_analysis(
            conn,
            condition="melanoma",
            treatment="miraclib",
            sample_type="PBMC",
            method=NEVER_SIGNIFICANT,
        )

    assert all(analysis.significant is True for analysis in significant_result)
    assert all(analysis.statistic == 0.0 for analysis in significant_result)
    assert all(analysis.significant is False for analysis in not_significant_result)
    assert all(analysis.statistic == 1.0 for analysis in not_significant_result)


def test_boxplot_stats_reflect_the_underlying_sample_data(engine):
    _setup_both_response_groups(engine)

    with engine.connect() as conn:
        [analysis] = [
            a
            for a in get_response_significance_analysis(
                conn,
                condition="melanoma",
                treatment="miraclib",
                sample_type="PBMC",
                method=ALWAYS_SIGNIFICANT,
            )
            if a.population == "b_cell"
        ]

    expected = pytest.approx(100 * COUNTS["b_cell"] / sum(COUNTS.values()))
    assert analysis.responder.median == expected
    assert analysis.non_responder.median == expected


def test_significance_test_receives_subject_level_not_sample_level_values(engine):
    # A subject with two samples for the same population should contribute
    # one collapsed value to the significance test, not two raw ones --
    # verified by inspecting what the stub method actually received.
    project_id = insert_project(engine)
    responder = insert_subject(engine, project_id, source_id="r", treatment_response="yes")
    non_responder = insert_subject(engine, project_id, source_id="nr", treatment_response="no")
    insert_sample(engine, responder, "s-r1", COUNTS)
    insert_sample(engine, responder, "s-r2", COUNTS)
    insert_sample(engine, non_responder, "s-nr", COUNTS)

    received: list[tuple[list[float], list[float]]] = []

    def spy_test(responder_values, non_responder_values):
        received.append((list(responder_values), list(non_responder_values)))
        return SignificanceResult(statistic=0.0, significant=True)

    spy_method = SignificanceMethod(name="spy", description="spy", test=spy_test)

    with engine.connect() as conn:
        get_response_significance_analysis(
            conn,
            condition="melanoma",
            treatment="miraclib",
            sample_type="PBMC",
            method=spy_method,
        )

    responder_values, non_responder_values = received[0]
    assert len(responder_values) == 1
    assert len(non_responder_values) == 1
