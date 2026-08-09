from app.repository.db import supabase
from app.models.responses import PaginatedTickets, TicketTableResponse



def get_tickets_table_paginated(page_number: int = 0, page_size: int = 10) -> TicketTableResponse:

    start = page_number * page_size # 0-based page number
    end = start + page_size - 1
    response = (
        supabase.table("ticket")
        .select("*", count="exact")
        .order("timestamp", desc=True)
        .range(start, end)
        .execute()
    )
    
    return TicketTableResponse(data=PaginatedTickets(items=response.data, page=page_number, page_size=page_size), count=response.count)