from fastapi import APIRouter, Depends
from sqlalchemy import Connection

from backend.core.db import get_connection
from backend.previsualizing.response_frequency_analysis import get_response_frequency_analysis
from backend.schemas.response_frequency_analysis import ResponseFrequencyAnalysis

router = APIRouter()


@router.get("/response-frequency-analysis", response_model=ResponseFrequencyAnalysis)
def read_response_frequency_analysis(
    condition: str,
    treatment: str,
    sample_type: str,
    median_threshold: float,
    conn: Connection = Depends(get_connection),
) -> ResponseFrequencyAnalysis:
    return get_response_frequency_analysis(
        conn,
        condition=condition,
        treatment=treatment,
        sample_type=sample_type,
        median_threshold=median_threshold,
    )
