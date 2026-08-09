from app.models.tickets import Ticket
from app.repository.table_repository import get_tickets_table_paginated



def get_ticket_table(page_number: int = 0, page_size: int = 10):
    return get_tickets_table_paginated(page_number=page_number, page_size=page_size)