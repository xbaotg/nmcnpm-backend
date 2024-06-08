from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date, time, datetime, timedelta

class EventAdd(BaseModel):
    match_id: int
    event_name : str
    seconds: str = "MM:SS"
    player_id: int
    # show: bool = True

class EventRes(BaseModel):
    match_id: int
    event_name: str
    seconds: int
    player_id: int

