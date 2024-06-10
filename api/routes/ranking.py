from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_, text

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Events, GoalTypes
from schemas.params import Show_Params, Update_Params, Annotated, GoalTypeAdd
from utils import (
    get_params,
)

route = APIRouter()


# RANKING BY SCORE
@route.get("/ranking-by-score")
async def ranking_by_score(db: db_deps):
    print("hello")
    return "hello"
