from pydantic import BaseModel
import time

class EventLog(BaseModel):
    user_id: str
    timestamp: float
    event: str

def log_event(user_id: str, event: str) -> EventLog:
    return EventLog(user_id=user_id, timestamp=time.time(), event=event)
