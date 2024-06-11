from datetime import date, datetime
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func
from api.deps import CurrentUser, List
from core.db import db as code_db
from core.db import db_deps
from schemas.db import Clubs, Players, Users, Events
from schemas.players import PlayerCreate, PlayerShow, PlayerUpdate, Player_Add_With_Club
from utils import is_valid_age, MIN_CLUB_PLAYER, MAX_CLUB_PLAYER

route = APIRouter()


def create_player_res(player):
    bday = None
    if player.player_bday is not None:
        bday = player.player_bday
    else:
        bday = player.player_bday
    return {
        # "status": "success",
        # "data": {
        "player_id": player.player_id,
        "player_name": player.player_name,
        "player_bday": bday,
        "player_club": player.player_club,
        "player_pos": player.player_pos,
        "player_nation": player.player_nation,
        "js_number": player.js_number,
        "ava_url": player.avatar_url,
        # },
    }

def create_player_res_with_goals(db:db_deps, player):
    bday = None
    if player.player_bday is not None:
        bday = player.player_bday
    else:
        bday = player.player_bday
    total_goals = db.query(Events).filter(Events.show==True, Events.player_id==player.player_id).count()
    return {
        # "status": "success",
        # "data": {
        "player_id": player.player_id,
        "player_name": player.player_name,
        "player_bday": bday,
        "player_club": player.player_club,
        "player_pos": player.player_pos,
        "player_nation": player.player_nation,
        "js_number": player.js_number,
        "total_goals": total_goals,
        "ava_url": player.avatar_url,
        # },
    }

def get_user_permission(db: db_deps, current_user: CurrentUser, role: str):
    if current_user is None:
        return {"status": "error", "message": "Authentication Failed"}

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role
    )

    if role == "manager":
        if (
            not db.query(Users)
            .filter(Users.user_id == current_user["user_id"])
            .first()
            .show
        ):
            return {"status": "error", "message": "Your account is no longer active!"}

        return {"status": "success"}
    elif role == "admin" and user_role != role:
        return {
            "status": "error",
            "message": "You don't have permission to do this action!",
        }

    return {"status": "success"}


@route.post("/add-players")
async def add_players(player: PlayerCreate, db: db_deps, current_user: CurrentUser):
    permission_result = get_user_permission(db, current_user, "admin")
    if permission_result["status"] == "error":
        return permission_result

    dup_player = (
        db.query(Players).filter(Players.player_name == player.player_name).first()
    )
    if dup_player is not None:
        if (
            dup_player.player_bday == player.player_bday
            and dup_player.player_club == player.player_club
            and dup_player.player_nation == player.player_nation
            and dup_player.player_pos == player.player_pos
            and dup_player.js_number == player.js_number
        ):
            return {"status": "error", "message": "Player already existed!"}

    try:
        newPlayerDict = player.dict()
        for key, value in newPlayerDict.items():
            if value == "string":
                return {"status": "error", "message": f"{key} is required."}
            if key == "player_bday" and not is_valid_age(value):
                return {"status": "error", "message": "Player age is not legal"}

        count = db.query(func.max(Players.player_id)).scalar()
        newPlayerDict["player_id"] = (count or 0) + 1
        new_db_player = Players(**newPlayerDict)

        club = (
            db.query(Clubs)
            .filter(Clubs.show == True, Clubs.club_id == player.player_club)
            .first()
        )
        if not club:
            return {"status": "error", "message": "Club not found"}
        if club.total_player + 1 > MAX_CLUB_PLAYER:
            return {
                "status": "error",
                "message": "Total player is larger than MAX_CLUB_PLAYER",
            }

        db.add(new_db_player)
        db.commit()
        db.refresh(new_db_player)

        club.total_player += 1
        db.commit()
        db.refresh(club)

        return create_player_res(new_db_player)

    except HTTPException as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


@route.get("/get-players")
async def get_players(
    db: db_deps,
    full_name: str = None,
    club_name: str = None,
    position: str = None,
    nation: str = None,
    threshold: int = 80,
):
    try:
        players = db.query(Players).filter(Players.show == True).all()

        if not players:
            return {"status": "error", "message": "No players found"}

        matched_players = players

        if full_name:
            matched_players = [
                player
                for player in matched_players
                if fuzz.partial_ratio(player.player_name.lower(), full_name.lower())
                >= threshold
            ]

        if club_name:
            active_club = db.query(Clubs).filter(Clubs.show == True).all()
            club_id = None

            for club in active_club:
                if (
                    fuzz.partial_ratio(club.club_name.lower(), club_name.lower())
                    >= threshold
                ):
                    club_id = club.club_id
                    break

            if club_id:
                matched_players = [
                    player
                    for player in matched_players
                    if player.player_club == club_id
                ]
            else:
                return {"status": "error", "message": "Cannot find club"}

        if position:
            matched_players = [
                player
                for player in matched_players
                if fuzz.partial_ratio(player.player_pos.lower(), position.lower())
                >= threshold
            ]

        if nation:
            matched_players = [
                player
                for player in matched_players
                if fuzz.partial_ratio(player.player_nation.lower(), nation.lower())
                >= threshold
            ]

        if not matched_players:
            return {"status": "error", "message": "Cannot find players"}

        res = [create_player_res_with_goals(db, player) for player in matched_players]

        return {"status": "success", "data": res}

    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


@route.put("/update-player")
async def update_player(
    playerID: int, player_update: PlayerUpdate, db: db_deps, current_user: CurrentUser
):
    try:
        target = db.query(Players).filter(Players.player_id == playerID).first()
        update_info = player_update.dict(exclude_unset=True)
        for key, value in update_info.items():
            if value == "string":
                return {"status": "error", "message": f"{key} is required."}
            if key == "player_bday" and not is_valid_age(value):
                return {"status": "error", "message": "User age is not legal"}
            setattr(target, key, value)
        db.commit()
        db.refresh(target)

        return create_player_res_with_goals(target)

    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}!"}


@route.put("/delete-player")
async def delete_player(playerID: int, current_user: CurrentUser, db: db_deps):
    permission_result = get_user_permission(db, current_user, "manager")
    if permission_result["status"] == "error":
        return permission_result

    try:
        target = db.query(Players).filter(Players.player_id == playerID).first()

        if target is None:
            return {
                "status": "error",
                "message": f"Can't find player with id:{playerID}",
            }

        if target.show == True:
            club = (
                db.query(Clubs)
                .filter(Clubs.show == True, Clubs.club_id == target.player_club)
                .first()
            )
            if not club:
                return {"status": "error", "message": "Club not found"}

            if club.total_player - 1 > MIN_CLUB_PLAYER:
                return {
                    "status": "error",
                    "message": "Total player is smaller than MIN_CLUB_PLAYER",
                }

            target.show = False
            db.commit()

            club.total_player -= 1
            db.commit()
            db.refresh(club)

            return {
                "status": "success",
                "message": f"Deleted player with id:{playerID}",
            }
        else:
            return {
                "status": "error",
                "message": f"Can't find player with id:{playerID}. Maybe deleted.",
            }

    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}!"}


@route.put("/restore-deleted-player")
async def restore_deleted_player(
    player_id: int, current_user: CurrentUser, db: db_deps
):
    permission_result = get_user_permission(db, current_user, "manager")
    if permission_result["status"] == "error":
        return permission_result

    try:
        target = db.query(Players).filter(Players.player_id == player_id).first()
        if target.show != True:
            club = (
                db.query(Clubs)
                .filter(Clubs.show == True, Clubs.club_id == target.player_club)
                .first()
            )
            if not club:
                return {"status": "error", "message": "Club not found"}
            if club.total_player + 1 > MAX_CLUB_PLAYER:
                return {
                    "status": "error",
                    "message": "Total player is larger than MAX_CLUB_PLAYER",
                }

            target.show = True
            db.commit()

            club.total_player += 1
            db.commit()
            db.refresh(club)

            return {
                "status": "success",
                "message": f"Restored player with id:{player_id}",
            }
        else:
            return {
                "status": "error",
                "message": f"Can't find player with id:{player_id}.",
            }
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}!"}


@route.delete("/permanently-delete-player")
async def permanently_delete_player(
    player_id: int, db: db_deps, current_user: CurrentUser
):
    permission_result = get_user_permission(db, current_user, "manager")
    if permission_result["status"] == "error":
        return permission_result

    target = db.query(Players).filter(Players.player_id == player_id).first()

    db.delete(target)
    db.commit()
    return {
        "status": "success",
        "message": f"Delete players with id {player_id} successfully!",
    }
