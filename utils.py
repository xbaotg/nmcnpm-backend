from datetime import date
from fastapi import HTTPException
from schemas.db import Users, Params, Players, Clubs
from core.db import db_deps
from api.deps import CurrentUser

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


def check_club_player(db: db_deps, total_player: int):
    if total_player < MIN_CLUB_PLAYER or total_player > MAX_CLUB_PLAYER:
        return False
    return True
