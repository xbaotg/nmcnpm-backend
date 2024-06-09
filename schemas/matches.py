from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date, time, datetime, timedelta


class AddMatch(BaseModel):
    team1: int
    team2: int
    start: int = datetime.now().timestamp()
    # finish:
    # goal1: int -> new match -> goal = None
    # goal2: int
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
    goal1: int = -1
    goal2: int = -1
    ref: int
    var: int
    lineman: int
