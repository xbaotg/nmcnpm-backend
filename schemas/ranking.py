from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date
from enum import Enum


class InitRank(BaseModel):
    club_id: int
    club_ranking: int | None
    club_points: int | None
    club_win: int | None
    club_draw: int | None
    club_lost: int | None
    club_goals: int | None
    club_gconcede: int | None
    club_gdif: int | None
    show: bool

    class Config:
        orm_mode = True


class Criteria(str, Enum):
    by_points = "points"
    by_goals = "goals"
    by_away_goals = "away_goals"
    by_gdif = "gdif"
    by_win = "win"
    by_draw = "draw"
    by_lost = "lost"


class RankingRes(BaseModel):
    club_id: int
    away_goals: int
    club_points: int
    club_win: int
    club_draw: int
    club_lost: int
    club_goals: int
    club_gconcede: int
    club_gdif: int
    show: bool
    next_match: int | None
    recent_matches: List[int]
