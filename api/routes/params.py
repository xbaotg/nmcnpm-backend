from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_, text

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Events, GoalTypes
from schemas.params import Show_Params, Update_Params, Annotated, GoalTypeAdd
from utils import (
    is_valid_age,
    count_age,
    check_foreign_player,
    check_club_player_num,
    auto_count_total_player,
    get_params,
)

route = APIRouter()


def count_goal_types(db: db_deps):
    count = db.query(GoalTypes).filter(GoalTypes.show == True).count()
    params = db.query(Params).filter(Params.id == 1).first()
    params.max_goal_types = count

    db.commit()
    return count


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
    count_goal_types(db)
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

    # CHECK IF THERE'S CONFLICT DATA
    # check club's player num (good to use)
    db_clubs = db.query(Clubs).filter(Clubs.show == True).all()
    for club in db_clubs:
        count = (
            db.query(Players)
            .filter(Players.show == True, Players.player_club == club.club_id)
            .count()
        )
        if count < new_info.min_club_player or count > new_info.max_club_player:
            response_info = {
                "message": "There's conflict data with new MIN/MAX players of a club, please change it first !",
                "New MAX PLAYERS": new_info.max_club_player,
                "New MIN PLAYERS": new_info.min_club_player,
                "Conflict": count,
            }
            raise HTTPException(status_code=409, detail=response_info)

        # check club's foreign players (good to use)
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
            response_info = {
                "message": "There's conflict data with new MIN/MAX foreign players of a club, please change it first !",
                "new max foreign players": new_info.max_foreign_player,
                "conflict": count,
            }
            raise HTTPException(status_code=409, detail=response_info)

        # check player age (Done)
    if new_info.max_player_age < new_info.min_player_age:
        raise HTTPException(status_code=400, detail="MAX AGE must higher than MIN AGE")
    db_players = db.query(Players).filter(Players.show == True).all()
    for player in db_players:
        if not is_valid_age(
            player.player_bday,
            db,
            new_info.min_player_age,
            new_info.max_player_age,
            True,
        ):
            conflict = count_age(player.player_bday)
            response_info = {
                "message": "There's conflict data with new MIN/MAX player age, please change it first !",
                "New min age": new_info.min_player_age,
                "New max age": new_info.max_player_age,
                "Conflict": conflict,
            }
            raise HTTPException(status_code=409, detail=response_info)

        # check max_goal_time (Done)
    db_events = db.query(Events).filter(Events.show == True).all()
    for event in db_events:
        if event.seconds > new_info.max_goal_time:
            response_info = {
                "message": "There's conflict data with MAX GOAL TIME, please change it first!",
                "New MAX GOAL TIME": new_info.max_goal_time,
                "Conflict": event.seconds,
            }
            raise HTTPException(status_code=409, detail=response_info)

        # check point win/draw/lose
    if not (
        new_info.points_win > new_info.points_draw
        and new_info.points_draw > new_info.points_lose
    ):
        raise HTTPException(
            status_code=409,
            detail="Points must be: points win > points draw > points lose",
        )

    # update info
    new_info_dict = new_info.dict()
    for key, value in new_info_dict.items():
        setattr(params, key, value)

    db.commit()

    db.refresh(params)

    return {"message": "Update parameters successfully"}, params


@route.post("/add-goal-type")
async def add_goal_type(db: db_deps, current_user: CurrentUser, new_goal_type: str):
    is_admin(db, current_user)
    duplicated = (
        db.query(GoalTypes)
        .filter(GoalTypes.show == True, GoalTypes.type_name == new_goal_type)
        .first()
    )

    if duplicated:
        raise HTTPException(status_code=406, detail="Type name already existed !")

    type_id = (1 + (db.query(func.max(GoalTypes.type_id)).scalar() or 0),)
    sql_command = text(
        """
    INSERT INTO goaltypes (type_id, type_name, show)
    VALUES (:type_id, :type_name, :show);
    """
    )
    try:
        result = db.execute(
            sql_command, {"type_id": type_id, "type_name": new_goal_type, "show": True}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()
    # Update max_goal_types
    count_goal_types(db)

    return {"message": "Goal type added successfully"}


@route.post("/delete-goal-type")
async def delete_goal_type(db: db_deps, current_user: CurrentUser, type_id: int):
    # find the goal type
    target = (
        db.query(GoalTypes)
        .filter(GoalTypes.show == True, GoalTypes.type_id == type_id)
        .first()
    )

    if not target:
        raise HTTPException(status_code=204, detail="Can't find goal type!")

    # if any event has this goal type
    conflict = (
        db.query(Events)
        .filter(Events.show == True, Events.event_name == target.type_name)
        .first()
    )
    if conflict:
        raise HTTPException(
            status_code=409,
            detail="There're events that has this goal type, can't delete",
        )
    target.show = False
    db.commit()
    db.refresh(target)

    return {"message": "Delete type successfully"}


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
