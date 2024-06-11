from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date, time, datetime, timedelta


class AddMatch(BaseModel):
    team1: int
    team2: int
    start: int = datetime.now().timestamp()
    finish: int = datetime.now().timestamp() + timedelta(days=36500).total_seconds()
    # finish:
    # goal1: int -> new match -> goal = None
    # goal2: int
    stadium: int
    goal1: int = 0
    goal2: int = 0
    ref: int
    var: int
    lineman: int
    # show: bool = True


class MatchResponse(BaseModel):
    # turn id(int) into name(str)
    match_id: int
    team1: int
    team2: int
    start: int
    finish: int | None
    stadium: int
    goal1: Optional[int] = None
    goal2: Optional[int] = None
    ref: int
    var: int
    lineman: int


class MatchUpdate(BaseModel):
    team1: int
    team2: int
    start: int
    finish: int
    stadium: int
    goal1: int = -1
    goal2: int = -1
    ref: int
    var: int
    lineman: int
