"""Boxplot summary stats of cell-population frequencies, split by response.

For subjects with a given condition and treatment, and samples of a given
type, computes the five-number summary (min, Q1, median, Q3, max) of each
population's relative frequency, separately for responding ("yes") and
non-responding ("no") subjects. Each Sample row matching the filters is one
data point -- same per-sample frequency computation as
crunching.cell_frequencies, just scoped and grouped differently.
"""

from dataclasses import dataclass
from statistics import quantiles

from sqlalchemy import Connection, select

from backend.crunching.cell_frequencies import POPULATIONS
from backend.models.tables import project, sample, subject


@dataclass(frozen=True)
class FrequencyBoxplotStats:
    population: str
    response: str
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float


def get_response_frequency_boxplot_stats(
    conn: Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
) -> list[FrequencyBoxplotStats]:
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
            # response in practice, but this filters out None defensively
            # rather than assuming that holds for every possible input.
            subject.c.treatment_response.is_not(None),
        )
    ).all()

    # frequencies[population][response] -> that group's per-sample percentages
    frequencies: dict[str, dict[str, list[float]]] = {
        population: {"yes": [], "no": []} for population in POPULATIONS
    }
    for row in rows:
        counts = {population: getattr(row, population) for population in POPULATIONS}
        total_count = sum(counts.values())
        for population, count in counts.items():
            frequencies[population][row.treatment_response].append(100 * count / total_count)

    result: list[FrequencyBoxplotStats] = []
    for population in POPULATIONS:
        for response, values in frequencies[population].items():
            if not values:
                continue
            if len(values) == 1:
                q1 = median = q3 = values[0]
            else:
                q1, median, q3 = quantiles(values, n=4, method="inclusive")
            result.append(
                FrequencyBoxplotStats(
                    population=population,
                    response=response,
                    minimum=min(values),
                    q1=q1,
                    median=median,
                    q3=q3,
                    maximum=max(values),
                )
            )
    return result
