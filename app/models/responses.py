from pydantic import BaseModel
from datetime import date
from app.models.enum import TicketStatus
class TrendPoint(BaseModel):
    happen: date
    violations: int

class TrendAnalysis(BaseModel):
    trend: list[TrendPoint]

class HistogramPoint(BaseModel):
    location: str
    violations: int

class LocationAnalysis(BaseModel):
    location_trend: list[HistogramPoint]



class MetricResponse(BaseModel):
    pie_chart: dict[TicketStatus, int]
    violations_today: int
    total_violations: int
    tickets_issued: int
    tickets_pending: int
    trend_analysis: list[TrendAnalysis]
    location_analysis: list[LocationAnalysis]
