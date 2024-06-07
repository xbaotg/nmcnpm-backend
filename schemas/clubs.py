from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date

from schemas.players import Player_Add_With_Club


class Club_Response(BaseModel):
    club_name: str
    club_shortname: str
    total_player: int
    manager: str  # convert id to name

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
