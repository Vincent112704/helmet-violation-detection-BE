from pydantic import BaseModel
from datetime import date
from app.models.enum import TicketStatus
class TrendPoint(BaseModel):
    happen: date
    violations: int

class HistogramPoint(BaseModel):
    location: str
    violations: int


class MetricResponse(BaseModel):
    pie_chart: dict[TicketStatus, int]
    violations_today: int
    total_violations: int
    tickets_issued: int
    tickets_pending: int
    tickets_appealed: int
    trend_analysis: list[TrendPoint]
    location_analysis: list[HistogramPoint]
