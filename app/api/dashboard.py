from fastapi import APIRouter,
from app.services.dashboard_service import aggregate_table_data
from app.repository.dashboard_repository import get_tickets_table

router = APIRouter()

@router.get('/')
async def test():
    res = get_tickets_table(30)
    return { "message": "success", status: 200, data: res} #change to json response

@router.get('/metrics')
async def get_metrics():
    return await aggregate_table_data()
