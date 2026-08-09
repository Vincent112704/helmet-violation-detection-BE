from fastapi import APIRouter
from app.services.dashboard_service import aggregate_table_data
from app.models.responses import MetricResponse

router = APIRouter()


@router.get('/metrics', response_model=MetricResponse)
def get_metrics():
    return aggregate_table_data()
