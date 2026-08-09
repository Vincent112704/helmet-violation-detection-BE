from app.repository.dashboard_repository import get_tickets_table
from app.models.responses import MetricResponse



def aggregate_table_data() -> MetricResponse:
    return get_tickets_table(30)