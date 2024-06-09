from pydantic import BaseModel
from typing import Optional
from datetime import date


class UserCreateBase(BaseModel):
    full_name: str
    role: str
    user_name: str
    password: str
    user_nation: str
    user_bday: date
    user_mail: str


class UserReg(BaseModel):
    user_id: int | None
    full_name: str | None
    role: str | None
    user_name: str | None
    user_mail: str | None
    user_nation: str | None
    user_bday: int
    show: bool | None

    class Config:
        orm_mode = True


class UserUpdate(BaseModel):
    full_name: str | None
    role: str | None
    user_name: str | None
    password: str | None
    user_nation: str | None
    user_bday: date | None
    user_mail: str | None
