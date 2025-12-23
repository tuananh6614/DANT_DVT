"""
Data Models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Card:
    card_id: str
    owner_name: str = ""
    plate_number: str = ""
    phone: str = ""
    is_active: bool = True


@dataclass
class Session:
    id: int
    card_id: str
    plate_number: str
    slot_number: int
    entry_time: datetime
    exit_time: Optional[datetime] = None
    fee: int = 0
    payment_status: str = "pending"
    
    @property
    def is_active(self) -> bool:
        return self.exit_time is None


@dataclass
class SlotStats:
    total: int
    occupied: int
    available: int
