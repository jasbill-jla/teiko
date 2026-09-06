"""Tests for backend.crunching.mann_whitney_significance.

Pure function -- no DB involved. Exercised through the public
MANN_WHITNEY_U.test interface, not the private _test helper.
"""

import pytest
from scipy.stats import mannwhitneyu

from backend.crunching.mann_whitney_significance import ALPHA, BONFERRONI_ALPHA, MANN_WHITNEY_U
from backend.crunching.cell_frequencies import POPULATIONS


def test_bonferroni_alpha_is_alpha_divided_by_population_count():
    assert BONFERRONI_ALPHA == ALPHA / len(POPULATIONS)


def test_clearly_separated_groups_are_significant():
    responder_values = [10.0, 11.0, 12.0, 9.0, 10.5, 11.5, 9.5, 10.2, 11.8, 9.8]
    non_responder_values = [50.0, 51.0, 52.0, 49.0, 50.5, 51.5, 49.5, 50.2, 51.8, 49.8]

    result = MANN_WHITNEY_U.test(responder_values, non_responder_values)

    assert 0.0 <= result.statistic <= 1.0
    assert result.statistic < BONFERRONI_ALPHA
    assert result.significant is True


def test_identical_distributions_are_not_significant():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    result = MANN_WHITNEY_U.test(list(values), list(values))

    assert result.statistic > BONFERRONI_ALPHA
    assert result.significant is False


def test_statistic_is_the_scipy_p_value_not_the_u_statistic():
    responder_values = [1.0, 2.0, 3.0, 4.0]
    non_responder_values = [10.0, 20.0, 30.0, 40.0]

    result = MANN_WHITNEY_U.test(responder_values, non_responder_values)

    _, expected_p_value = mannwhitneyu(responder_values, non_responder_values, alternative="two-sided")
    assert result.statistic == expected_p_value


def test_significant_iff_statistic_below_bonferroni_alpha():
    responder_values = [1.0, 2.0, 3.0, 4.0]
    non_responder_values = [10.0, 20.0, 30.0, 40.0]

    result = MANN_WHITNEY_U.test(responder_values, non_responder_values)

    assert result.significant == (result.statistic < BONFERRONI_ALPHA)


def test_description_documents_the_active_alpha():
    assert MANN_WHITNEY_U.name == "Mann-Whitney U test"
    assert f"p < {BONFERRONI_ALPHA:.3g}" in MANN_WHITNEY_U.description
