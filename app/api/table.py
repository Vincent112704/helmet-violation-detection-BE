from fastapi import APIRouter
from app.services.table_service import get_ticket_table
from app.models.responses import TicketTableResponse

router = APIRouter()



@router.get('/tickets', response_model=TicketTableResponse)
def get_tickets(page_number: int = 0, page_size: int = 10):
    return get_ticket_table(page_number=page_number, page_size=page_size)
