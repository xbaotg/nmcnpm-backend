from pydantic import BaseModel
from typing import List, Annotated, Optional
from datetime import date


class UserCreateBase(BaseModel):
    fullname: str
    role: str  
    user_name : str 
    password: str 
    user_nation: str 
    user_bday: date
    user_mail: str 

class User_res(BaseModel):
    userid: int
    fullname: str
    role : str
    user_name : str
    user_mail : str
    user_bday: date
    show: bool
    class Config: 
        orm_mode = True
    
class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    role: Optional[str] = None
    user_name: Optional[str] = None
    password: Optional[str] = None
    user_nation: Optional[str] = None
    user_bday: Optional[date] = None
    user_mail: Optional[str] = None
    user_nation: Optional[str] = None