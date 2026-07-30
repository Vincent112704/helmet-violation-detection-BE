from app.repository.db import supabase
from app.models.tickets import Ticket
from app.models.responses import MetricResponse


def get_tickets_table() -> list[Ticket]:
    pass


#TODO:
#  - update query should be db-side not server-side
#  - add appropriate sql files
