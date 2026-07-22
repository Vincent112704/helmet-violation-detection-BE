from fastapi import APIRouter
from app.services.table_service import get_ticket_table
router = APIRouter()


@router.get('/table-test')
async def test():
    return {'message': 'table test success'}

@router.get('/tickets')
async def get_tickets():
    return await get_ticket_table()
