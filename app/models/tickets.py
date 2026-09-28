from datetime import datetime
from app.models.enum import TicketStatus
from uuid import UUID
from typing import Optional
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


class ViolationUpdate(BaseModel):
    location: Optional[str] = None
    status: Optional[TicketStatus] = None
    plate_number: Optional[str] = None