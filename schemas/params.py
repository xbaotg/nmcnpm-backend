from pydantic import BaseModel, Field
from typing import List, Annotated
from datetime import time, datetime


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
    max_goal_time: time

    class Config:
        orm_mode = True


class Update_Params(BaseModel):
    # id: int
    min_player_age: int | None
    max_player_age: int | None
    min_club_player: int | None
    max_club_player: int | None
    max_foreign_player: int | None

    points_win: int | None
    points_draw: int | None
    points_lose: int | None

    max_goal_types: int | None
    max_goal_time: time = time(1, 30)

    class Config:
        orm_mode = True
