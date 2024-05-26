from pydantic import BaseModel
from typing import Optional
from datetime import date

class Club_Response(BaseModel):
    club_name: str
    club_shortname: str
    total_player: int
    nation: str
    manager: str # convert id to name
    
    # show: bool
    # club_id: int
    class Config:
        orm_mode = True

class Club_Create(BaseModel):
    club_name: str
    club_shortname: str
    # total_player: int # default = 0 
    
    nation: str
    # manager: int # automatically take from the one create new club
    # show: bool # default = True
