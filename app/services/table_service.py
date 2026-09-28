from app.models.tickets import Ticket
from app.repository.table_repository import get_tickets_table_paginated, delete_ticket_data, patch_ticket_data
from app.models.tickets import ViolationUpdate


def get_ticket_table(page_number: int = 0, page_size: int = 10):
    return get_tickets_table_paginated(page_number=page_number, page_size=page_size)

def delete_ticket_service(ticket_id: str):
    data = delete_ticket_data(ticket_id)

    if not data: 
        return None

    return data


def patch_ticket_service(ticket_id: str, violation: dict):
    data = patch_ticket_data(ticket_id, violation)

    if not data: 
        return None
    
    return data