from pydantic import BaseModel
from datetime import date


class RefCreate(BaseModel):
    ref_name: str
    ref_bday: int
    ref_nation: str
    ref_mail: str
    show: bool = True


class RefShow(BaseModel):
    ref_name: str
    ref_bday: int
    ref_nation: str
    ref_mail: str


class RefUpdate(BaseModel):
    ref_name: str
    ref_bday: int
    ref_nation: str
    ref_mail: str
    show: bool = True
