"""Per-sample cell-population frequencies grouped by treatment response.

Shared data pull for analyses that compare responding vs. non-responding
subjects -- built once here so each such analysis (e.g.
response_frequency_stats.get_response_frequency_boxplot_stats) works from
the same underlying data instead of re-querying Sample/Subject/Project.
"""

from statistics import median

from sqlalchemy import Connection, select

from backend.crunching.cell_frequencies import POPULATIONS
from backend.models.tables import project, sample, subject

# population -> response ("yes"/"no") -> that group's per-sample percentages.
# A population/response combination with no matching samples is absent from
# its inner dict entirely, never present with an empty list.
ResponseFrequencies = dict[str, dict[str, list[float]]]


def get_response_frequencies(
    conn: Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
) -> ResponseFrequencies:
    """Per-population, per-response lists of per-sample relative frequencies.

    Scoped to subjects with the given condition and treatment, and samples of
    the given type. Each qualifying Sample row contributes one percentage per
    population, same computation as crunching.cell_frequencies.
    """
    rows = conn.execute(
        select(
            subject.c.treatment_response,
            sample.c.b_cell,
            sample.c.cd8_t_cell,
            sample.c.cd4_t_cell,
            sample.c.nk_cell,
            sample.c.monocyte,
        )
        .select_from(sample.join(subject).join(project))
        .where(
            subject.c.condition_name == condition,
            subject.c.treatment_name == treatment,
            project.c.sample_type == sample_type,
            # Subjects matching a real condition/treatment always have a
            # response in practice, but this filters None out defensively
            # rather than assuming that holds for every possible input.
            subject.c.treatment_response.is_not(None),
        )
    ).all()

    frequencies: ResponseFrequencies = {population: {} for population in POPULATIONS}
    for row in rows:
        counts = {population: getattr(row, population) for population in POPULATIONS}
        total_count = sum(counts.values())
        for population, count in counts.items():
            frequencies[population].setdefault(row.treatment_response, []).append(
                100 * count / total_count
            )
    return frequencies


def get_response_median_frequencies(
    frequencies: ResponseFrequencies,
) -> dict[str, dict[str, float]]:
    """Per-population median frequency for each response group present.

    Pure function over get_response_frequencies's output -- no DB access.
    A population with no samples for a given response simply has no entry
    for that response (or no entry at all if neither response has samples).
    """
    return {
        population: {response: median(values) for response, values in by_response.items()}
        for population, by_response in frequencies.items()
        if by_response
    }


def get_significant_response_populations(
    median_frequencies: dict[str, dict[str, float]],
    threshold: float,
) -> list[str]:
    """Populations whose responder/non-responder median frequencies differ by
    at least `threshold` percentage points.

    A population missing either response group (no "yes" or no "no" samples)
    can't be compared and is excluded rather than treated as significant or
    insignificant. Returned in the fixed POPULATIONS order, not dict order.
    """
    return [
        population
        for population in POPULATIONS
        if "yes" in median_frequencies.get(population, {})
        and "no" in median_frequencies.get(population, {})
        and abs(median_frequencies[population]["yes"] - median_frequencies[population]["no"])
        >= threshold
    ]
