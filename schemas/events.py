from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date, time, datetime, timedelta

class EventAdd(BaseModel):
    match_id: int
    event_name : str
    minute_event: str = "HH:MM"
    player_id: int
    # show: bool = True

