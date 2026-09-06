"""Shapes response-frequency crunching output into the API response.

Pulls the raw per-sample frequency data once and derives both parts of the
response from it (medians for every comparable population, boxplot stats for
only the ones whose median difference clears the threshold) rather than
querying twice.
"""

from sqlalchemy import Connection

from backend.crunching.response_frequencies import (
    get_response_frequencies,
    get_response_median_frequencies,
    get_significant_response_populations,
)
from backend.crunching.response_frequency_stats import compute_boxplot_stats
from backend.schemas.response_frequency_analysis import (
    BoxplotStats,
    PopulationBoxplot,
    PopulationMedianFrequencies,
    ResponseFrequencyAnalysis,
)


def get_response_frequency_analysis(
    conn: Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
    median_threshold: float,
) -> ResponseFrequencyAnalysis:
    frequencies = get_response_frequencies(
        conn, condition=condition, treatment=treatment, sample_type=sample_type
    )
    median_frequencies = get_response_median_frequencies(frequencies)
    significant_populations = get_significant_response_populations(
        median_frequencies, median_threshold
    )
    boxplot_stats = compute_boxplot_stats(frequencies, significant_populations)

    medians = [
        PopulationMedianFrequencies(
            population=population,
            responder_median=by_response["yes"],
            non_responder_median=by_response["no"],
        )
        for population, by_response in median_frequencies.items()
        if "yes" in by_response and "no" in by_response
    ]

    # Pair up the flat (population, response) boxplot rows into one
    # two-sided structure per population. Every population reaching this
    # point has both response groups present (guaranteed by
    # get_significant_response_populations), so both lookups always succeed.
    stats_by_population: dict[str, dict[str, BoxplotStats]] = {}
    for stat in boxplot_stats:
        stats_by_population.setdefault(stat.population, {})[stat.response] = BoxplotStats(
            minimum=stat.minimum,
            q1=stat.q1,
            median=stat.median,
            q3=stat.q3,
            maximum=stat.maximum,
        )

    boxplots = [
        PopulationBoxplot(
            population=population,
            responder=by_response["yes"],
            non_responder=by_response["no"],
        )
        for population, by_response in stats_by_population.items()
    ]

    return ResponseFrequencyAnalysis(medians=medians, boxplots=boxplots)
