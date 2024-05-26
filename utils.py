from datetime import date
from fastapi import HTTPException
from schemas.db import Users, Params, Players
from schemas.players import Player_Add_With_Club
from core.db import db_deps

# tam thoi la fixed value, se update lai khi xong table params
MIN_PLAYER_AGE = 16
MAX_PLAYER_AGE = 40
MIN_CLUB_PLAYER = 2
MAX_CLUB_PLAYER = 22
MAX_FOREIGN_PLAYER = 3
POINTS_WIN = 2
POINTS_DRAW = 1
POINTS_LOSE = 0
MAX_GOAL_TYPES = 3
MAX_GOAL_TIME = "01:30:00"

def is_valid_age(bday: date):
    now = date.today()
    age = now.year - bday.year - ((now.month, now.day) < (bday.month, bday.day))

    # try:
    #     db = db_deps
    #     stats = db_deps.query(Params).first()

    #     min_age = stats.MIN_PLAYER_AGE
    #     max_age = stats.MAX_PLAYER_AGE
    # except Exception as e:
    #     raise HTTPException(status_code=501, detail=f"Error: {str(e)}")

    if age < MIN_PLAYER_AGE or age > MAX_PLAYER_AGE:
        return False

    return True

async def create_club_add_player(db: db_deps, club_id: int, new_player: Player_Add_With_Club):
    count = 0
    while (count < MIN_CLUB_PLAYER):

        count += 1
