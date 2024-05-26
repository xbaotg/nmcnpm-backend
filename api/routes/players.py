from datetime import date

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func

from api.deps import CurrentUser, List
from core.db import db as code_db
from core.db import db_deps
from schemas.db import Clubs, Players, Users
from schemas.players import PlayerCreate, PlayerShow, PlayerUpdate

route = APIRouter()


def get_user_permission(db: db_deps, current_user: CurrentUser, role: str):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    # check permission of user_role
    if role == "manager":
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
    elif role == "admin" and user_role != role:
        raise HTTPException(
            status_code=401, detail="You don't have permission to do this action!"
        )

    return True


def isValidAge(bday: date):
    now = date.today()
    age = now.year - bday.year - ((now.month, now.day) < (bday.month, bday.day))
    if age < 16 or age > 40:
        return False
    return True


@route.post("/add_players")
async def add_players(player: PlayerCreate, db: db_deps):  # current_user: CurrentUser):
    try:
        # hasPermission = get_user_permission(current_user, db, "manager")
        newPlayerDict = player.dict()
        for key, value in newPlayerDict.items():
            if value == "string":
                return {"message": f"{key} is required."}
            if key == "player_bday" and not isValidAge(value):
                return {"message": "User age is not legal"}

        count = db.query(func.max(Players.player_id)).scalar()
        newPlayerDict["player_id"] = (count or 0) + 1
        new_db_player = Players(**newPlayerDict)

        db.add(new_db_player)
        db.commit()
        db.refresh(new_db_player)
        return new_db_player

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@route.get("/get_players_by_name", response_model=List[PlayerShow])
async def get_players_by_name(full_name: str, db: db_deps, threshold: int = 80):
    try:
        players = db.query(Players).filter(Players.show == True).all()
        matched_players = [
            player
            for player in players
            if fuzz.partial_ratio(player.player_name.lower(), full_name.lower())
            >= threshold
        ]

        if not matched_players:
            raise HTTPException(status_code=404, detail="Cannot find players")

        return matched_players
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@route.get("/get_players_by_club", response_model=List[PlayerShow])
async def get_players_by_club(club_name: str, db: db_deps, threshold: int = 80):
    try:
        active_club = db.query(Clubs).filter(Clubs.show == True).all()
        club_id = None
        for club in active_club:
            if (
                fuzz.partial_ratio(club.club_name.lower(), club_name.lower())
                >= threshold
            ):
                club_id = club.club_id
                break

        if club_id is None:
            raise HTTPException(status_code=404, detail="Cannot find club")

        players = db.query(Players).filter(Players.show == True).all()
        matched_players = [
            player for player in players if player.player_club == club_id
        ]
        if not matched_players:
            raise HTTPException(status_code=404, detail="Cannot find players")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    return matched_players


@route.get("/get_players_by_pos", response_model=List[PlayerShow])
async def get_players_by_pos(position: str, db: db_deps, threshold: int = 80):
    try:
        players = db.query(Players).filter(Players.show == True).all()
        matched_players = [
            player
            for player in players
            if fuzz.partial_ratio(player.player_pos.lower(), position.lower())
            >= threshold
        ]
        if not matched_players:
            raise HTTPException(status_code=404, detail="Cannot find players")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    return matched_players


@route.get("/get_players_by_nation", response_model=List[PlayerShow])
async def get_players_by_nation(nation: str, db: db_deps, threshold: int = 80):
    try:
        players = db.query(Players).filter(Players.show == True).all()
        matched_players = [
            player
            for player in players
            if fuzz.partial_ratio(player.player_nation.lower(), nation.lower())
            >= threshold
        ]
        if not matched_players:
            raise HTTPException(status_code=404, detail="Cannot find players")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    return matched_players


@route.put("/update_player")
async def update_player(
    playerID: int, player_update: PlayerUpdate, db: db_deps
):  # current_user: CurrentUser):
    try:
        # hasPermission = get_user_permission(current_user, db, "manager")
        target = db.query(Players).filter(Players.player_id == playerID).first()
        update_info = player_update.dict(exclude_unset=True)
        for key, value in update_info.items():
            if value == "string":
                return {"message": f"{key} is required."}
            if key == "player_bday" and not isValidAge(value):
                return {"message": "User age is not legal"}
            setattr(target, key, value)
        db.commit()
        db.refresh(target)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}!")
    return target
