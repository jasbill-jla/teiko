"""Pydantic response shapes for the response-frequency-analysis endpoint."""

from pydantic import BaseModel


class BoxplotStats(BaseModel):
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float


class PopulationBoxplot(BaseModel):
    population: str
    responder: BoxplotStats
    non_responder: BoxplotStats
    # The comparable statistic behind `significant` (e.g. a p-value) -- not
    # a raw test statistic like Mann-Whitney U's U value, whose scale isn't
    # comparable across populations with different sample sizes.
    statistic: float
    significant: bool


class ResponseFrequencyAnalysis(BaseModel):
    # Plain-language explanation of how `significant` was determined, e.g.
    # which test and threshold were used -- sourced from whichever
    # significance method is active, so this stays accurate if that changes.
    methodology: str
    boxplots: list[PopulationBoxplot]
