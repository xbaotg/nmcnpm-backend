from pydantic import BaseModel
from typing import List, Annotated
from datetime import date


class PlayerCreate(BaseModel):
    player_name: str
    player_bday: int
    player_club: int
    player_pos: str
    player_nation: str
    js_number: int
    show: bool = True


class PlayerShow(BaseModel):
    player_name: str
    player_bday: int | None
    player_club: int
    player_pos: str
    player_nation: str
    js_number: int
    player_id: int


class PlayerUpdate(BaseModel):
    player_name: str
    player_bday: date
    player_club: int
    js_number: int
    player_pos: str
    show: bool = True


class Player_Add_With_Club(BaseModel):
    player_name: str
    player_bday: date
    # player_club: int
    player_pos: str
    player_nation: str
    js_number: int
    # show: bool = True
