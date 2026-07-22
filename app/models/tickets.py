from datetime import datetime
from app.models.enum import TicketStatus
from uuid import UUID

from pydantic import BaseModel


#Database model
class Ticket(BaseModel):
    ticket_id: UUID
    officer: UUID
    status: TicketStatus
    plate_number: str | None = None
    location: str
    timestamp: datetime
    url: str | None = None

#Update Ticket request for false alarms

class UpdateTicketStatusRequest(BaseModel):
    status: TicketStatus