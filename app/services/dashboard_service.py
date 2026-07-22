from app.repository.dashboard_repository import get_tickets_table
from app.models.responses import MetricResponse


def aggregate_table_data() -> MetricResponse:
    '''
        metrics to measure:
          - By status type (pie chart)
          - Violations recorded today (KPI card)
          - Total Violations (KPI card)
          - Tickets issued (KPI Card)
          - Tickets pending (KPI card)
          - Trend analysis (violations per time)
          - Violation location across Dumaguete (Histogram)

    '''
    tickets = get_tickets_table()
    

    return {"message": "hello"}