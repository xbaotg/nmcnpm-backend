
from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date, time, datetime, timedelta

class AddMatch(BaseModel):
    team1: str | int
    team2: str | int
    start: str = str(datetime.now().strftime(f"%H:%M %d/%m/%Y")) 
    # finish: 
    # goal1: int -> new match -> goal = None
    # goal2: int
    ref: int | str
    var: int | str
    lineman: int | str
    # show: bool = True


class MatchResponse(BaseModel):  
    # turn id(int) into name(str)
    team1: str
    team2: str
    start: str
    goal1: Optional[int] = None
    goal2: Optional[int] = None
    ref: str
    var: str
    lineman: str
