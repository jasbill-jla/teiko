"""Pydantic response shapes for the response-frequency-analysis endpoint."""

from pydantic import BaseModel


class PopulationMedianFrequencies(BaseModel):
    population: str
    responder_median: float
    non_responder_median: float


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


class ResponseFrequencyAnalysis(BaseModel):
    medians: list[PopulationMedianFrequencies]
    boxplots: list[PopulationBoxplot]
