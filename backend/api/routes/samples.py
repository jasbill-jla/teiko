from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Connection

from backend.core.db import get_connection
from backend.previsualizing.samples import get_field_values, get_samples_result
from backend.schemas.samples import SamplesResult

router = APIRouter()


@router.get("/samples", response_model=SamplesResult)
def read_samples(
    grouping: Literal["project", "subject"] | None = None,
    condition: str | None = None,
    treatment: str | None = None,
    sample_type: str | None = None,
    time_from_treatment: int | None = None,
    group_count_field: Literal["sex", "response"] | None = None,
    conn: Connection = Depends(get_connection),
) -> SamplesResult:
    if grouping == "subject" and group_count_field is None:
        raise HTTPException(
            status_code=422,
            detail="group_count_field ('sex' or 'response') is required when grouping is 'subject'",
        )
    return get_samples_result(
        conn,
        condition=condition,
        treatment=treatment,
        sample_type=sample_type,
        time_from_treatment=time_from_treatment,
        grouping=grouping,
        group_count_field=group_count_field,
    )


@router.get("/samples/field-values", response_model=list[str])
def read_samples_field_values(
    field: Literal["condition", "treatment", "sample_type", "time_from_treatment"],
    conn: Connection = Depends(get_connection),
) -> list[str]:
    return get_field_values(conn, field=field)
