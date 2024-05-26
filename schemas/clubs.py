from pydantic import BaseModel

class ClubCreate(BaseModel):
    club_id : int
    club_name :  str
    total_player : int
    nation : str
    manager : int
    club_shortname : str 
    show : bool = True

class ClubShow(BaseModel):
    club_name :  str
    nation : str
    manager : int
    club_shortname : str 

class ClubUpdate(BaseModel):
    club_name :  str
    total_player : int
    nation : str
    manager : int
    club_shortname : str 
    show : bool = True