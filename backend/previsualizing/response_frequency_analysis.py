"""Shapes response-significance crunching output into the API response."""

from sqlalchemy import Connection

from backend.crunching.mann_whitney_significance import MANN_WHITNEY_U
from backend.crunching.response_frequency_stats import FrequencyBoxplotStats
from backend.crunching.response_significance import get_response_significance_analysis
from backend.schemas.response_frequency_analysis import (
    BoxplotStats,
    PopulationBoxplot,
    ResponseFrequencyAnalysis,
)

# The active significance method. Swapping which test is used is a one-line
# change here -- both the API response's `methodology` text and the
# frontend read the method's own `description` rather than hardcoding which
# test is active, so nothing downstream needs to change to swap it.
SIGNIFICANCE_METHOD = MANN_WHITNEY_U


def _to_schema(stats: FrequencyBoxplotStats) -> BoxplotStats:
    return BoxplotStats(
        minimum=stats.minimum,
        q1=stats.q1,
        median=stats.median,
        q3=stats.q3,
        maximum=stats.maximum,
    )


def get_response_frequency_analysis(
    conn: Connection,
    *,
    condition: str,
    treatment: str,
    sample_type: str,
) -> ResponseFrequencyAnalysis:
    analyses = get_response_significance_analysis(
        conn,
        condition=condition,
        treatment=treatment,
        sample_type=sample_type,
        method=SIGNIFICANCE_METHOD,
    )

    boxplots = [
        PopulationBoxplot(
            population=analysis.population,
            responder=_to_schema(analysis.responder),
            non_responder=_to_schema(analysis.non_responder),
            statistic=analysis.statistic,
            significant=analysis.significant,
        )
        for analysis in analyses
    ]

    return ResponseFrequencyAnalysis(methodology=SIGNIFICANCE_METHOD.description, boxplots=boxplots)
