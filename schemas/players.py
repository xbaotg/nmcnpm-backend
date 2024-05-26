from pydantic import BaseModel
# from typing import List, Annotated, Optionals
from datetime import date

class PlayerCreate(BaseModel):
    player_id: int
    player_name: str
    player_bday: date
    player_club: int
    player_pos: str
    player_nation : str
    js_number : int
    show: bool = True

class PlayerShow(BaseModel):
    player_name: str
    player_bday: date
    player_club: int
    player_pos: str
    player_nation : str
    js_number : int

class PlayerUpdate(BaseModel):
    player_name: str
    player_bday: date
    player_club: int
    js_number: int
    player_pos: str
    show : bool = True