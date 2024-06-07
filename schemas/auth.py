from pydantic import BaseModel
from datetime import date, datetime


class CreateUserRequest(BaseModel):
    user_name: str
    password: str
    full_name: str
    user_nation: str
    user_bday: date
    user_mail: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expired_date: int
