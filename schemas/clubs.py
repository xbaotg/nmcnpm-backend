from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date

from schemas.players import Player_Add_With_Club


class Club_Response(BaseModel):
    club_id: int
    club_name: str
    club_shortname: str
    total_player: int
    manager_id: int
    manager_name: str
    logo_high: str | None
    logo_low: str | None

    # show: bool
    # club_id: int
    class Config:
        orm_mode = True


class Club_Create(BaseModel):
    club_name: str
    club_shortname: str
    # total_player: int # default = 0

    # manager: int # automatically take from the one create new club
    # show: bool # default = True
    club_players: List[Player_Add_With_Club]


class Club_Update(BaseModel):
    club_name: str
    club_shortname: str
    # total_player: int

    # show: bool
    # club_id: int
