"""Per-population boxplot stats plus a pluggable significance test.

Boxplot stats come from per-sample frequencies (a five-number summary is
descriptive, not inferential, so it doesn't need independent observations).
The significance test uses per-subject frequencies instead, since inferential
tests assume independent observations, which per-sample values violate
whenever a subject contributes more than one sample.
"""

from dataclasses import dataclass

from sqlalchemy import Connection

from backend.crunching.cell_frequencies import POPULATIONS
from backend.crunching.response_frequencies import (
    get_response_frequencies,
    get_response_subject_frequencies,
)
from backend.crunching.response_frequency_stats import FrequencyBoxplotStats, compute_boxplot_stats
from backend.crunching.significance import SignificanceMethod


@dataclass(frozen=True)
class PopulationResponseAnalysis:
    population: str
    responder: FrequencyBoxplotStats
    non_responder: FrequencyBoxplotStats
    statistic: float
    significant: bool


def get_response_significance_analysis(
    conn: Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
    method: SignificanceMethod,
) -> list[PopulationResponseAnalysis]:
    """One entry per population with data on both sides, in POPULATIONS order.

    A population missing either response group entirely (no matching "yes"
    or "no" samples/subjects) is omitted -- there's nothing to compare or
    test. For a real condition/treatment/sample_type combination this
    shouldn't happen for some populations and not others (every Sample row
    contributes a value to every population at once), but isn't assumed.
    """
    frequencies = get_response_frequencies(
        conn, condition=condition, treatment=treatment, sample_type=sample_type
    )
    subject_frequencies = get_response_subject_frequencies(
        conn, condition=condition, treatment=treatment, sample_type=sample_type
    )

    boxplot_stats = compute_boxplot_stats(frequencies, POPULATIONS)
    boxplot_by_population: dict[str, dict[str, FrequencyBoxplotStats]] = {}
    for stat in boxplot_stats:
        boxplot_by_population.setdefault(stat.population, {})[stat.response] = stat

    result: list[PopulationResponseAnalysis] = []
    for population in POPULATIONS:
        by_response = boxplot_by_population.get(population, {})
        responder_subjects = subject_frequencies.get(population, {}).get("yes", [])
        non_responder_subjects = subject_frequencies.get(population, {}).get("no", [])
        if (
            "yes" not in by_response
            or "no" not in by_response
            or not responder_subjects
            or not non_responder_subjects
        ):
            continue
        significance = method.test(responder_subjects, non_responder_subjects)
        result.append(
            PopulationResponseAnalysis(
                population=population,
                responder=by_response["yes"],
                non_responder=by_response["no"],
                statistic=significance.statistic,
                significant=significance.significant,
            )
        )
    return result
