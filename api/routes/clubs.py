from datetime import date
from sqlalchemy import func

from core.db import db_deps
from fastapi import APIRouter, HTTPException, Depends
from schemas.db import Clubs, Users, Players
from schemas.clubs import Club_Response, Club_Create, Club_Update
from schemas.players import PlayerShow
from crud import create_club as crud_create_club

from api.deps import List, CurrentUser, get_password_hash, fuzz
from utils import check_owner, check_is_manager, get_user_role, auto_count_total_player

from loguru import logger

route = APIRouter()


@route.get("/get-all-clubs")
async def get_all_clubs(db: db_deps):
    try:
        db_clubs = db.query(Clubs).filter(Clubs.show == True).all()

        if not db_clubs:
            return {"status": "error", "message": "Can't find players of club"}

        result = []

        for club in db_clubs:
            manager = db.query(Users).filter(Users.user_id == club.manager).first()
            manager_full_name = manager.full_name
            manager_id = manager.user_id

            if not manager_full_name:
                return {
                    "status": "error",
                    "message": f"Can't find manager of club: {club.club_name}",
                }

            auto_count_total_player(db, club.club_id)

            club_data = {
                "club_id": club.club_id,
                "club_name": club.club_name,
                "club_shortname": club.club_shortname,
                "total_player": club.total_player,
                "manager_name": manager_full_name,
                "manager_id": manager_id,
                "logo_high": club.logo_high,
                "logo_low": club.logo_low,
            }

            result.append(club_data)

        return {
            "status": "success",
            "message": "Clubs retrieved successfully",
            "data": result,
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error(f"Server Error: {str(e)}")
        return {"status": "error", "message": f"Server Error: {str(e)}"}


@route.get("/search-club-by-name")
async def search_club_by_name(db: db_deps, search_name: str, threshold: int = 80):
    db_clubs = db.query(Clubs).filter(Clubs.show == True).all()

    if not db_clubs:
        return {"status": "error", "message": "Can't find any clubs"}

    result = []
    for club in db_clubs:
        ratio = fuzz.partial_ratio(club.club_name.lower(), search_name.lower())
        if ratio < threshold:
            continue

        manager_full_name = (
            db.query(Users).filter(Users.user_id == club.manager).first().full_name
        )
        if not manager_full_name:
            return {
                "status": "error",
                "message": f"Can't find manager of club: {club.club_name}",
            }
        club_data = Club_Response(
            club_id=club.club_id,
            club_name=club.club_name,
            club_shortname=club.club_shortname,
            total_player=club.total_player,
            manager_id=club.manager,
            manager_name=manager_full_name,
        )
        result.append(club_data)

    if len(result) == 0:
        return {"status": "error", "message": f"No clubs match the name: {search_name}"}

    return {
        "status": "success",
        "message": "Clubs retrieved successfully",
        "data": result,
    }


@route.get("/search-club-by-manager-id")
async def search_club_by_manager_id(db: db_deps, manager_search_id: int):

    target = (
        db.query(Users)
        .filter(
            Users.show == True,
            Users.user_id == manager_search_id,
            Users.role == "manager",
        )
        .first()
    )
    if target is None:
        return {"status": "error", "message": "Can't find manager"}

    manager_full_name = (
        db.query(Users).filter(Users.user_id == manager_search_id).first().full_name
    )

    db_clubs = (
        db.query(Clubs)
        .filter(Clubs.show == True, Clubs.manager == manager_search_id)
        .all()
    )
    if not db_clubs:
        return {"status": "error", "message": "This manager doesn't have any clubs"}

    result = []
    for club in db_clubs:
        club_data = Club_Response(
            club_id=club.club_id,
            club_name=club.club_name,
            club_shortname=club.club_shortname,
            total_player=club.total_player,
            manager_id=club.manager,
            manager_name=manager_full_name,
        )
        result.append(club_data)

    return {
        "status": "success",
        "message": "Clubs retrieved successfully",
        "data": result,
    }


@route.get("/get-players-of-clubs/{club_name}")
async def get_all_players_of_clubs(db: db_deps, club_name: str):
    db_clubs = db.query(Clubs).filter(Clubs.show == True).all()

    search_club = None
    for club in db_clubs:
        len_ = len(club_name) / len(club.club_name)
        if (
            fuzz.partial_ratio(club.club_name.lower(), club_name.lower()) >= 98
            and len_ >= 0.6
            and len_ <= 1.0
        ):
            search_club = club

    if not search_club:
        return {"status": "error", "message": "Can't find any clubs"}

    db_players = (
        db.query(Players)
        .filter(Players.player_club == search_club.club_id, Players.show == True)
        .all()
    )
    if db_players:
        res = []
        for player in db_players:
            player_res = PlayerShow(**vars(player))
            res.append(player_res)
        return {
            "status": "success",
            "message": "Players retrieved successfully",
            "data": res,
        }
    else:
        return {
            "status": "error",
            "message": f"Can't find any players of club with name {club_name}!",
        }


@route.post("/create-club")
async def create_club(db: db_deps, current_user: CurrentUser, new_club: Club_Create):
    try:
        hasPermission = check_is_manager(db, current_user)
        created_club = crud_create_club(db, current_user, new_club)
        return {
            "status": "success",
            "message": "Club created successfully",
            "data": created_club,
        }
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


@route.put("/update-club/{club_name}")
async def update_club(
    db: db_deps, current_user: CurrentUser, club_name: str, new_info: Club_Update
):
    try:
        clubs = db.query(Clubs).filter(Clubs.show == True).all()

        search_club = None
        for club in clubs:
            len_ = len(club_name) / len(club.club_name)
            if (
                fuzz.partial_ratio(club.club_name.lower(), club_name.lower()) >= 98
                and len_ >= 0.6
                and len_ <= 1.0
            ):
                search_club = club

        if search_club is None:
            return {"status": "error", "message": "Can't find any clubs"}

        club_id = search_club.club_id

        user_role = get_user_role(db, current_user)
        is_owner = check_owner(db, current_user, club_id)
        if is_owner is None:
            return {
                "status": "error",
                "message": f"Can't find the club with ID {club_id}!",
            }
        if not is_owner and user_role == "manager":
            return {"status": "error", "message": "You are not the owner of this club"}

        target = db.query(Clubs).filter(Clubs.club_id == club_id).first()
        update_info = new_info.dict(exclude_unset=True)
        for key, value in update_info.items():
            if value == "string":
                continue
            setattr(target, key, value)
        db.commit()
        db.refresh(target)
        return {
            "status": "success",
            "message": "Club updated successfully",
            "data": target,
        }
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


@route.delete("/delete-club")
async def delete_club(db: db_deps, current_user: CurrentUser, club_name: str):
    try:
        db_clubs = db.query(Clubs).filter(Clubs.show == True).all()

        search_club = None
        for club in db_clubs:
            len_ = len(club_name) / len(club.club_name)
            if (
                fuzz.partial_ratio(club.club_name.lower(), club_name.lower()) >= 100
                and len_ >= 0.9
                and len_ <= 1.0
            ):
                search_club = club

        if search_club is None:
            return {"status": "error", "message": "Can't find any clubs"}

        club_id = search_club.club_id

        user_role = get_user_role(db, current_user)
        is_owner = check_owner(db, current_user, club_id)
        if is_owner is None:
            return {
                "status": "error",
                "message": f"Can't find the club with ID {club_id}!",
            }
        if not is_owner and user_role == "manager":
            return {"status": "error", "message": "You are not the owner of this club"}

        players_of_clubs = (
            db.query(Players)
            .filter(Players.player_club == club_id, Players.show == True)
            .all()
        )
        for player in players_of_clubs:
            player.show = False
        db.commit()

        target = (
            db.query(Clubs).filter(Clubs.club_id == club_id, Clubs.show == True).first()
        )
        target.show = False
        db.commit()

        return {
            "status": "success",
            "message": f"Deleted {club_name} and all players of it!",
        }
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


@route.put("/restore-club")
async def restore_club(db: db_deps, current_user: CurrentUser, club_name: str):
    try:
        db_clubs = db.query(Clubs).filter(Clubs.show == False).all()

        search_club = None
        for club in db_clubs:
            len_ = len(club_name) / len(club.club_name)
            if (
                fuzz.partial_ratio(club.club_name.lower(), club_name.lower()) >= 100
                and len_ >= 0.9
                and len_ <= 1.0
            ):
                search_club = club

        if search_club is None:
            return {"status": "error", "message": "Can't find any clubs"}

        club_id = search_club.club_id

        user_role = get_user_role(db, current_user)
        is_owner = check_owner(db, current_user, club_id)
        if is_owner is None:
            return {
                "status": "error",
                "message": f"Can't find the club with ID {club_id}!",
            }
        if not is_owner and user_role == "manager":
            return {"status": "error", "message": "You are not the owner of this club"}

        players_of_clubs = (
            db.query(Players)
            .filter(Players.player_club == club_id, Players.show == False)
            .all()
        )
        for player in players_of_clubs:
            player.show = True
        db.commit()

        target = (
            db.query(Clubs)
            .filter(Clubs.club_id == club_id, Clubs.show == False)
            .first()
        )
        target.show = True
        db.commit()

        return {
            "status": "success",
            "message": f"Restored {club_name} and all players of it!",
        }
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}
