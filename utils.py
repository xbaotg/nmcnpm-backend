from datetime import date
from fastapi import HTTPException
from schemas.db import Users, Params, Players, Clubs
from core.db import db_deps, get_params, db
from api.deps import CurrentUser
from schemas.params import Show_Params

params = get_params(Params, db)
# default values
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


def is_valid_age(
    bday: date, db: db = db, MIN: int = 16, MAX: int = 40, overwrite: bool = False
):
    if not overwrite:
        params = get_params(Params, db)
        MIN_PLAYER_AGE = params.min_player_age
        MAX_PLAYER_AGE = params.max_player_age
    else:
        MIN_PLAYER_AGE = MIN
        MAX_PLAYER_AGE = MAX

    # params = get_params(Params, db)
    # MIN_PLAYER_AGE = params.min_player_age
    # MAX_PLAYER_AGE = params.max_player_age
    now = date.today()
    age = now.year - bday.year - ((now.month, now.day) < (bday.month, bday.day))
    print("age = ", age)
    print("min age: ", MIN_PLAYER_AGE)
    if age < MIN_PLAYER_AGE or age > MAX_PLAYER_AGE:
        return False

    return True


def get_user_role(db: db_deps, current_user: CurrentUser):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    return user_role


def check_is_manager(db: db_deps, current_user: CurrentUser):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    # check permission of user_role
    if user_role == "manager":
        # check if user is deleted or not
        if (
            not db.query(Users)
            .filter(Users.user_id == current_user["user_id"])
            .first()
            .show  # type: ignore
        ):
            raise HTTPException(
                status_code=401, detail="Your account is no longer active!"
            )

        return True
    elif user_role == "admin":
        raise HTTPException(
            status_code=203, detail="Admins doesn't have permission to create club"
        )

    return True


def check_owner(db: db_deps, current_user: CurrentUser, club_id: int):
    club = db.query(Clubs).filter(Clubs.club_id == club_id).first()
    if club is None:
        return None
    if current_user["user_id"] == club.manager:
        return True

    return False


# Use when add or delete a player from club
def check_club_player_num(db: db_deps, total_player: int):
    params = get_params(Params, db)
    MIN_CLUB_PLAYER = params.min_club_player
    MAX_CLUB_PLAYER = params.max_club_player
    if total_player < MIN_CLUB_PLAYER or total_player > MAX_CLUB_PLAYER:
        return False
    return True


# Use when add a player to a club
def check_foreign_player(db: db_deps, count: int):
    params = get_params(Params, db)
    MAX_FOREIGN_PLAYER = params.max_foreign_player

    if count <= MAX_FOREIGN_PLAYER:
        return True, MAX_FOREIGN_PLAYER
    else:
        return False, MAX_FOREIGN_PLAYER


def auto_count_total_player(db: db_deps, club_id: int):
    count = (
        db.query(Players)
        .filter(Players.show == True, Players.player_club == club_id)
        .count()
    )

    target = (
        db.query(Clubs).filter(Clubs.show == True, Clubs.club_id == club_id).first()
    )
    if not target:
        raise HTTPException(status_code=204, detail="Can't find any clubs")

    target.total_player = count
    db.commit()
    return count
