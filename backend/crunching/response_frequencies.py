"""Per-sample and per-subject cell-population frequencies, by response.

Shared data pulls for analyses that compare responding vs. non-responding
subjects -- built once here so each such analysis (e.g.
response_significance.get_response_significance_analysis) works from the
same underlying data instead of re-querying Sample/Subject/Project.
"""

from statistics import median

from sqlalchemy import Connection, select

from backend.crunching.cell_frequencies import POPULATIONS
from backend.models.tables import project, sample, subject

# population -> response ("yes"/"no") -> that group's per-X percentages,
# where X is "sample" or "subject" depending on which function produced it.
# A population/response combination with no matching data is absent from its
# inner dict entirely, never present with an empty list.
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

    One value per *sample*, not per subject -- appropriate for descriptive
    stats (e.g. a five-number summary for a boxplot), which don't require
    independent observations. Inferential statistics do; use
    get_response_subject_frequencies for those instead.
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


def get_response_subject_frequencies(
    conn: Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
) -> ResponseFrequencies:
    """Per-population, per-response lists of per-subject relative frequencies.

    Same scope and filters as get_response_frequencies, but one value per
    *subject* -- the median across that subject's own samples -- rather than
    one value per sample. A subject who contributes multiple samples (e.g.
    at different time points) is not an independent observation per sample;
    inferential tests like Mann-Whitney U assume independence, which this
    collapse restores. Descriptive stats (boxplots) don't need this and
    should keep using get_response_frequencies's per-sample values instead.

    Deliberately re-queries rather than aggregating get_response_frequencies's
    output, since that output has already discarded which sample belongs to
    which subject -- the two functions pull at genuinely different grains.
    """
    rows = conn.execute(
        select(
            subject.c.id.label("subject_id"),
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
            subject.c.treatment_response.is_not(None),
        )
    ).all()

    # population -> response -> subject_id -> that subject's per-sample percentages
    per_subject: dict[str, dict[str, dict[int, list[float]]]] = {
        population: {} for population in POPULATIONS
    }
    for row in rows:
        counts = {population: getattr(row, population) for population in POPULATIONS}
        total_count = sum(counts.values())
        for population, count in counts.items():
            by_subject = per_subject[population].setdefault(row.treatment_response, {})
            by_subject.setdefault(row.subject_id, []).append(100 * count / total_count)

    return {
        population: {
            response: [median(values) for values in by_subject.values()]
            for response, by_subject in by_response.items()
        }
        for population, by_response in per_subject.items()
    }
