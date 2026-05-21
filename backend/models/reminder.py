from pydantic import BaseModel
from typing import Optional


class ReminderSettings(BaseModel):
    user_id: str
    phone_number: str
    cutoff_hour: int = 21
    enabled: bool = True

class PublishRecord(BaseModel):
    title: str
    date: str
    platforms: list[str]
    status: str
    author: Optional[str] = "Anonymous Developer"
    
