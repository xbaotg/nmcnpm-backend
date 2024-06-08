from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date, time, datetime, timedelta


class EventAdd(BaseModel):
    match_id: int
    events: str
    seconds: int
    player_id: int
    # show: bool = True
