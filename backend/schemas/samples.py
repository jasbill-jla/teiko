"""Pydantic response shapes for the samples-browsing endpoint."""

from pydantic import BaseModel


class SampleRecord(BaseModel):
    project_source_id: str
    condition: str | None
    treatment: str | None
    subject_source_id: str
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


class GroupCount(BaseModel):
    # The project source_id, sex, or response value this count is for.
    # A subject with no response (e.g. an untreated/healthy subject that
    # slipped through because condition/treatment weren't used to filter)
    # groups under the literal string "none", not null or "".
    group: str
    count: int


class SamplesResult(BaseModel):
    samples: list[SampleRecord]
    counts: list[GroupCount]
