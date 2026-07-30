from app.repository.db import supabase
from app.models.tickets import Ticket
from app.models.responses import MetricResponse


def get_tickets_table(days_back) -> MetricResponse:
    res = supabase.rpc("dashboard_metrics", {"days_back": days_back}).execute()
    return MetricResponse.model_validate(res.data)


