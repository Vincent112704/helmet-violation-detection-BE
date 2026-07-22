from fastapi import APIRouter
from app.services.dashboard_service import aggregate_table_data
router = APIRouter()

@router.get('/dashboard-test')
async def test():
    return { "message": "dashboard test success"}

@router.get('/metrics')
async def get_metrics():
    return await aggregate_table_data()