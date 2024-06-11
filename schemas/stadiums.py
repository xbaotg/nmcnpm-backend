from pydantic import BaseModel
from typing import Optional, List, Annotated
from datetime import date, time, datetime, timedelta


class StadiumAdd(BaseModel):
    std_name: str
    cap: int