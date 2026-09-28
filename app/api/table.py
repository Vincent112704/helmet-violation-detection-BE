from fastapi import APIRouter, Response, HTTPException
from app.services.table_service import get_ticket_table, delete_ticket_service, patch_ticket_service
from app.models.responses import TicketTableResponse
from app.models.tickets import ViolationUpdate



router = APIRouter()




@router.get('/tickets', response_model=TicketTableResponse)
def get_tickets(page_number: int = 0, page_size: int = 10):
    return get_ticket_table(page_number=page_number, page_size=page_size)

@router.delete('/tickets/violation')
def delete_ticket(ticket_id: str):
    data = delete_ticket_service(ticket_id)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return Response(status_code=204)

@router.patch('/tickets/violation')
def patch_ticket(ticket_id: str, violation: ViolationUpdate):
    updates = violation.model_dump(exclude_unset=True)

    data = patch_ticket_service(ticket_id, updates)

    if not data:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return Response(status_code=204)


