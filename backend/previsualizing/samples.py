"""Sorts crunching.samples.get_samples's output and computes group counts.

The count unit follows the grouping, not the field within it: grouping by
project counts sample rows per project; grouping by subject (whether the
group_count_field is "sex" or "response") counts distinct subjects, not
samples, since a subject's multiple samples shouldn't inflate a subject-level
count.
"""

from typing import Literal

from sqlalchemy import Connection

from backend.crunching.samples import SampleDetail, get_samples
from backend.schemas.samples import GroupCount, SampleRecord, SamplesResult

Grouping = Literal["project", "subject"]
GroupCountField = Literal["sex", "response"]

# Sentinel label for a subject with no recorded response (e.g. untreated or
# healthy) -- distinguishes "no response" from the real values "yes"/"no".
NO_RESPONSE = "none"


def _to_schema(detail: SampleDetail) -> SampleRecord:
    return SampleRecord(
        project_source_id=detail.project_source_id,
        condition=detail.condition,
        treatment=detail.treatment,
        subject_source_id=detail.subject_source_id,
        age=detail.age,
        sex=detail.sex,
        response=detail.response,
        sample_type=detail.sample_type,
        time_from_treatment=detail.time_from_treatment,
        b_cell=detail.b_cell,
        cd8_t_cell=detail.cd8_t_cell,
        cd4_t_cell=detail.cd4_t_cell,
        nk_cell=detail.nk_cell,
        monocyte=detail.monocyte,
    )


def _sample_counts(groups: list[str]) -> list[GroupCount]:
    counts: dict[str, int] = {}
    for group in groups:
        counts[group] = counts.get(group, 0) + 1
    return [GroupCount(group=group, count=count) for group, count in counts.items()]


def _subject_counts(details: list[SampleDetail], group_of) -> list[GroupCount]:
    # One entry per distinct subject, keeping the group of its first
    # appearance -- a subject's samples all share the same sex/response
    # anyway, so which sample "wins" doesn't matter.
    group_by_subject: dict[str, str] = {}
    for detail in details:
        group_by_subject.setdefault(detail.subject_source_id, group_of(detail))
    return _sample_counts(list(group_by_subject.values()))


def get_samples_result(
    conn: Connection,
    *,
    condition: str | None,
    treatment: str | None,
    sample_type: str | None,
    time_from_treatment: int | None,
    grouping: Grouping,
    group_count_field: GroupCountField | None,
) -> SamplesResult:
    details = get_samples(
        conn,
        condition=condition,
        treatment=treatment,
        sample_type=sample_type,
        time_from_treatment=time_from_treatment,
    )

    if grouping == "project":
        details.sort(key=lambda d: (d.project_source_id, d.subject_source_id))
        counts = _sample_counts([d.project_source_id for d in details])
    elif group_count_field == "sex":
        details.sort(key=lambda d: (d.sex, d.subject_source_id))
        counts = _subject_counts(details, lambda d: d.sex)
    else:
        details.sort(key=lambda d: (d.response or NO_RESPONSE, d.subject_source_id))
        counts = _subject_counts(details, lambda d: d.response or NO_RESPONSE)

    return SamplesResult(
        samples=[_to_schema(detail) for detail in details],
        counts=counts,
    )
