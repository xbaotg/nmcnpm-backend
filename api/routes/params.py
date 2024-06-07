from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params
from schemas.params import Show_Params, Update_Params, Annotated
from utils import (
    is_valid_age,
    check_foreign_player,
    check_club_player_num,
    auto_count_total_player,
    get_params,
)

route = APIRouter()


def is_admin(db: db_deps, current_user: CurrentUser):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    # check permission of user_role
    if user_role != "admin":
        raise HTTPException(
            status_code=401, detail="You don't have permission to do this action!"
        )

    return True


# GET
@route.get("/show-params/", response_model=Show_Params)
async def show_params(db: db_deps, current_user: CurrentUser):
    is_admin(db, current_user)
    try:
        params = db.query(Params).first()
        return params
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# UPDATE
@route.put("/update-params/")
async def update_params(
    db: db_deps, current_user: CurrentUser, new_info: Update_Params
):
    # Admin only
    is_admin(db, current_user)
    try:
        params = db.query(Params).first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

    # check if there're conflict data
    # check club's player num (debugging)
    db_clubs = db.query(Clubs).filter(Clubs.show == True).all()
    for club in db_clubs:
        count = (
            db.query(Players)
            .filter(Players.show == True, Players.player_club == club.club_id)
            .count()
        )
        if count < new_info.min_club_player or count > new_info.max_club_player:
            print(f"{new_info.min_club_player} : {count} : {new_info.max_club_player}")
            conflict = True
            db.rollback()
            return {
                "message": "There's conflict data with new MIN/MAX players of a club, please change it first !"
            }

        # check club's foreign players (debugging)
        count = (
            db.query(Players)
            .filter(
                Players.show == True,
                Players.player_club == club.club_id,
                Players.player_nation != "VIE",
            )
            .count()
        )
        if count > new_info.max_foreign_player:
            conflict = True
            db.rollback()
            return {
                "message": "There's conflict data with new MIN/MAX foreign players of a club, please change it first !"
            }

        # check player age (good to use now)
    db_players = db.query(Players).filter(Players.show == True).all()
    for player in db_players:
        if not is_valid_age(
            player.player_bday,
            db,
            new_info.min_player_age,
            new_info.max_player_age,
            True,
        ):
            conflict = True
            db.rollback()
            return {
                "message": "There's conflict data with new MIN/MAX player age, please change it first !"
            }

    # update info
    new_info_dict = new_info.dict()
    for key, value in new_info_dict.items():
        if value == 0:
            continue
        if key == "max_goal_time" and value == params.max_goal_time:
            continue
        setattr(params, key, value)

    db.commit()

    db.refresh(params)

    return params


# default values
# {
#   "min_player_age": 16,
#   "max_player_age": 40,
#   "min_club_player": 15,
#   "max_club_player": 22,
#   "max_foreign_player": 3,
#   "points_win": 2,
#   "points_draw": 1,
#   "points_lose": 0,
#   "max_goal_types": 3,
#   "max_goal_time": "01:30:00"
# }
