"""Boxplot summary stats of cell-population frequencies, split by response.

Restricted to the cell populations whose responder vs. non-responder median
frequency differs by more than a caller-supplied threshold -- see
crunching.response_frequencies for the three building blocks this composes:
the raw per-sample data pull, the per-population medians, and the
significance filter itself.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from statistics import quantiles

from sqlalchemy import Connection

from backend.crunching.response_frequencies import (
    ResponseFrequencies,
    get_response_frequencies,
    get_response_median_frequencies,
    get_significant_response_populations,
)


@dataclass(frozen=True)
class FrequencyBoxplotStats:
    population: str
    response: str
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float


def compute_boxplot_stats(
    frequencies: ResponseFrequencies,
    populations: Iterable[str],
) -> list[FrequencyBoxplotStats]:
    """Five-number summary per population/response, for the given populations.

    Pure function over get_response_frequencies's output -- no DB access.
    Callers that already have `frequencies` (e.g. because they also need
    get_response_median_frequencies on it) should use this directly instead
    of get_response_frequency_boxplot_stats, to avoid querying twice.
    """
    result: list[FrequencyBoxplotStats] = []
    for population in populations:
        for response, values in frequencies[population].items():
            if len(values) == 1:
                q1 = response_median = q3 = values[0]
            else:
                q1, response_median, q3 = quantiles(values, n=4, method="inclusive")
            result.append(
                FrequencyBoxplotStats(
                    population=population,
                    response=response,
                    minimum=min(values),
                    q1=q1,
                    median=response_median,
                    q3=q3,
                    maximum=max(values),
                )
            )
    return result


def get_response_frequency_boxplot_stats(
    conn: Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
    significance_threshold: float,
) -> list[FrequencyBoxplotStats]:
    """Five-number summary per population/response, significant populations only.

    A cell population is included only if its responder vs. non-responder
    median frequency differs by more than `significance_threshold`
    percentage points (see get_significant_response_populations);
    populations that don't clear that bar, or that are missing one of the
    two response groups entirely, are omitted rather than returned as
    empty/zeroed rows.
    """
    frequencies = get_response_frequencies(
        conn, condition=condition, treatment=treatment, sample_type=sample_type
    )
    medians = get_response_median_frequencies(frequencies)
    significant_populations = get_significant_response_populations(
        medians, significance_threshold
    )
    return compute_boxplot_stats(frequencies, significant_populations)
