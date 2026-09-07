"""Pulls Sample rows (joined with Subject and Project) matching optional filters.

Each row carries the full detail the samples-browsing endpoint needs:
the project's source_id, the subject's demographics/condition/treatment/
response, and the sample's own type/time/cell-population counts. Filtering
only -- sorting and grouping/counting are view-specific and live in
previsualizing.samples.
"""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import Connection, select

from backend.models.tables import project, sample, subject

FilterableField = Literal["condition", "treatment", "sample_type", "time_from_treatment"]

_COLUMN_BY_FIELD = {
    "condition": subject.c.condition_name,
    "treatment": subject.c.treatment_name,
    "sample_type": project.c.sample_type,
    "time_from_treatment": sample.c.time_from_treatment,
}


@dataclass(frozen=True)
class SampleDetail:
    project_source_id: str
    subject_source_id: str
    condition: str | None
    treatment: str | None
    age: int
    sex: str
    response: str | None
    sample_type: str
    time_from_treatment: int
    b_cell: int
    cd8_t_cell: int
    cd4_t_cell: int
    nk_cell: int
    monocyte: int


def get_samples(
    conn: Connection,
    *,
    condition: str | None,
    treatment: str | None,
    sample_type: str | None,
    time_from_treatment: int | None,
) -> list[SampleDetail]:
    """Samples matching every given filter; a `None` filter doesn't restrict.

    Condition and treatment are nullable (a healthy/untreated subject has no
    value recorded) -- an empty-string filter for either matches those rows
    (IS NULL) rather than a literal empty value, which never occurs in the
    data.
    """
    filters = []
    if condition == "":
        filters.append(subject.c.condition_name.is_(None))
    elif condition is not None:
        filters.append(subject.c.condition_name == condition)
    if treatment == "":
        filters.append(subject.c.treatment_name.is_(None))
    elif treatment is not None:
        filters.append(subject.c.treatment_name == treatment)
    if sample_type is not None:
        filters.append(project.c.sample_type == sample_type)
    if time_from_treatment is not None:
        filters.append(sample.c.time_from_treatment == time_from_treatment)

    rows = conn.execute(
        select(
            project.c.source_id.label("project_source_id"),
            subject.c.source_id.label("subject_source_id"),
            subject.c.condition_name.label("condition"),
            subject.c.treatment_name.label("treatment"),
            subject.c.age,
            subject.c.sex,
            subject.c.treatment_response.label("response"),
            project.c.sample_type,
            sample.c.time_from_treatment,
            sample.c.b_cell,
            sample.c.cd8_t_cell,
            sample.c.cd4_t_cell,
            sample.c.nk_cell,
            sample.c.monocyte,
        )
        .select_from(sample.join(subject).join(project))
        .where(*filters)
    ).all()

    return [
        SampleDetail(
            project_source_id=row.project_source_id,
            subject_source_id=row.subject_source_id,
            condition=row.condition,
            treatment=row.treatment,
            age=row.age,
            sex=row.sex,
            response=row.response,
            sample_type=row.sample_type,
            time_from_treatment=row.time_from_treatment,
            b_cell=row.b_cell,
            cd8_t_cell=row.cd8_t_cell,
            cd4_t_cell=row.cd4_t_cell,
            nk_cell=row.nk_cell,
            monocyte=row.monocyte,
        )
        for row in rows
    ]


def get_field_values(conn: Connection, *, field: FilterableField) -> list[str | int | None]:
    """Distinct values recorded for one of the samples filters.

    Includes `None` when some row has no value for the field (e.g. a
    healthy/untreated subject's condition/treatment) -- sample_type and
    time_from_treatment are never null, so this only surfaces for those two.
    """
    column = _COLUMN_BY_FIELD[field]
    rows = conn.execute(
        select(column).select_from(sample.join(subject).join(project)).distinct()
    ).all()
    return [row[0] for row in rows]
