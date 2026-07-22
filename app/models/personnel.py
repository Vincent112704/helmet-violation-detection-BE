from uuid import UUID
from pydantic import BaseModel
from app.models.enum import UserRole

class Personnel(BaseModel):
    id: UUID
    display_name: str
    email: str
    role: UserRole