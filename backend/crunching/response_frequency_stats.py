"""Boxplot summary stats of cell-population frequencies, split by response.

Pure -- takes crunching.response_frequencies.get_response_frequencies's
output as input rather than querying the DB itself, so callers that also
need other analyses on the same data (e.g. a significance test) don't pay
for two queries.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from statistics import quantiles

from backend.crunching.response_frequencies import ResponseFrequencies


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

    A population/response combination absent from `frequencies` (no matching
    samples) is simply omitted from the result rather than returned as an
    empty/zeroed row.
    """
    result: list[FrequencyBoxplotStats] = []
    for population in populations:
        for response, values in frequencies.get(population, {}).items():
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
