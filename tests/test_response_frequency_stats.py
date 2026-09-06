"""Tests for backend.crunching.response_frequency_stats.compute_boxplot_stats.

Pure function -- no DB involved.
"""

from statistics import median

import pytest

from backend.crunching.response_frequency_stats import compute_boxplot_stats


def test_five_number_summary_matches_min_max_median():
    values = [2.0, 30.0, 9.0, 41.0, 15.0, 8.0, 23.0]
    frequencies = {"b_cell": {"yes": values}}

    [stats] = compute_boxplot_stats(frequencies, ["b_cell"])

    assert stats.population == "b_cell"
    assert stats.response == "yes"
    assert stats.minimum == min(values)
    assert stats.maximum == max(values)
    assert stats.median == pytest.approx(median(values))
    assert stats.minimum <= stats.q1 <= stats.median <= stats.q3 <= stats.maximum


def test_single_value_group_has_all_five_stats_equal():
    frequencies = {"b_cell": {"yes": [42.0]}}

    [stats] = compute_boxplot_stats(frequencies, ["b_cell"])

    assert stats.minimum == stats.q1 == stats.median == stats.q3 == stats.maximum == 42.0


def test_covers_every_response_group_present_for_each_requested_population():
    frequencies = {
        "b_cell": {"yes": [1.0, 2.0, 3.0], "no": [4.0, 5.0, 6.0]},
        "cd8_t_cell": {"yes": [7.0, 8.0, 9.0]},
    }

    stats = compute_boxplot_stats(frequencies, ["b_cell", "cd8_t_cell"])

    keys = {(s.population, s.response) for s in stats}
    assert keys == {("b_cell", "yes"), ("b_cell", "no"), ("cd8_t_cell", "yes")}


def test_population_absent_from_frequencies_is_skipped_not_errored():
    frequencies = {"b_cell": {"yes": [1.0, 2.0, 3.0]}}

    stats = compute_boxplot_stats(frequencies, ["b_cell", "nk_cell"])

    assert [s.population for s in stats] == ["b_cell"]


def test_only_requested_populations_are_included():
    frequencies = {
        "b_cell": {"yes": [1.0, 2.0]},
        "cd8_t_cell": {"yes": [3.0, 4.0]},
    }

    stats = compute_boxplot_stats(frequencies, ["b_cell"])

    assert [s.population for s in stats] == ["b_cell"]
