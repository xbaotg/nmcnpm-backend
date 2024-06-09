from pydantic import BaseModel, Field
from typing import List, Annotated
from datetime import time, datetime
from utils import get_params, db
from schemas.db import Params, GoalTypes

params = get_params(Params, db)


class Show_Params(BaseModel):
    # id: int
    min_player_age: int
    max_player_age: int
    min_club_player: int
    max_club_player: int
    max_foreign_player: int

    points_win: int
    points_draw: int
    points_lose: int

    max_goal_types: int
    max_goal_time: int

    class Config:
        orm_mode = True


class Update_Params(BaseModel):
    # id: int
    min_player_age: int = params.min_player_age
    max_player_age: int = params.max_player_age
    min_club_player: int = params.min_club_player
    max_club_player: int = params.max_club_player
    max_foreign_player: int = params.max_foreign_player

    points_win: int = params.points_win
    points_draw: int = params.points_draw
    points_lose: int = params.points_lose

    # max_goal_types: int = params.max_goal_types -> config in another endpoint
    max_goal_time: int = params.max_goal_time

    class Config:
        orm_mode = True


class GoalTypeAdd(BaseModel):
    type_id: int
    type_name: str
    show: bool
