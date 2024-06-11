from pydantic import BaseModel
from typing import Optional
from datetime import date


class UserCreateBase(BaseModel):
    full_name: str
    role: str
    user_name: str
    password: str
    user_nation: str
    user_bday: int
    user_mail: str


class UserCreateBaseResponse(BaseModel):
    status: str
    message: str
    data: UserCreateBase


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


class UserRegResponse(BaseModel):
    status: str
    message: str
    data: UserReg


class UserUpdate(BaseModel):
    full_name: str | None
    role: str | None
    user_name: str | None
    password: str | None
    user_nation: str | None
    user_bday: int | None
    user_mail: str | None


class UserUpdateResponse(BaseModel):
    status: str
    message: str
    data: UserUpdate
