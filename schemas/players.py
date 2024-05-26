from pydantic import BaseModel
from typing import Optional
from datetime import date

class Player_Add_With_Club(BaseModel):
    player_name: str
    player_bday: date
    # player_club: int 
    player_pos: str
    player_nation: str
    js_number: int
    # show : True
    
