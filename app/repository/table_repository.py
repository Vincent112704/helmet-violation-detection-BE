from app.repository.db import supabase
from app.models.responses import PaginatedTickets, TicketTableResponse
import logging



logging.basicConfig(level=logging.INFO)


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

def delete_ticket_data(ticket_id: str):
    try:
        response = (
            supabase.table("ticket")
            .delete()
            .eq("ticket_id", ticket_id)
            .execute()
        )
        return {"message": "success"}

    except Exception as e:
        logging.error(f"There was an error deleting the ticket")
        return {"error": str(e)}

def patch_ticket_data(ticket_id: str, violation: dict):
    try:
        response = (
            supabase.table("ticket")
            .update(violation)
            .eq("ticket_id", ticket_id)
            .execute()
        )

        return {"message": "success"}
    
    except Exception as e:
        logging.error("There was an error updating ticket table")
        return {"error": str(e)}