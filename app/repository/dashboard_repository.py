from app.repository.db import supabase
from app.models.tickets import Ticket

def get_tickets_table() -> list[Ticket]:
    response = supabase.table('ticket').select('*').execute()
    return [ Ticket.model_validate(row) for row in response.data]