from enum import Enum


#Database enum models

class UserRole(str, Enum):
    OFFICER = "officer"
    SUPERVISOR = "supervisor"

class TicketStatus(str, Enum):
    PENDING = "pending"
    ISSUED = "issued"
    FALSE_ALARM = "false_alarm"