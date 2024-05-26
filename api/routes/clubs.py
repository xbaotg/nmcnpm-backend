from datetime import date
from sqlalchemy import func

from core.db import db_deps
from fastapi import APIRouter, HTTPException, Depends
from schemas.db import Clubs, Users
from schemas.clubs import Club_Response, Club_Create
from crud import create_club as crud_create_club


from api.deps import List, CurrentUser, get_password_hash, fuzz

route = APIRouter()

def check_is_manager(db: db_deps, current_user : CurrentUser):
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

@route.get("/get-all-clubs", response_model=List[Club_Response])
async def get_all_clubs(db: db_deps):
    try:
        db_clubs = db.query(Clubs).filter(Clubs.show==True).all()
        if not db_clubs:
            raise HTTPException(status_code=204, detail="Can't find players of club")
        result = []

        # get manager's full name from manager's id
        for club in db_clubs:
            manager_full_name = db.query(Users).filter(Users.user_id == club.manager).first().full_name
            if not manager_full_name:
                raise HTTPException(status_code=204, detail= f"Can't find manager of club: {club.club_name}")
            club_data = {
                "club_name": club.club_name,
                "club_shortname": club.club_shortname,
                "total_player": club.total_player,
                "nation": club.nation,
                "manager": manager_full_name
            }
            result.append(club_data)

        return result

    except Exception as e:
        raise HTTPException(status_code=501, detail=f"Server Error: {str(e)}")
    

@route.get("search-club-by-name", response_model=List[Club_Response] | dict)
async def search_club_by_name(db: db_deps, search_name: str, threshold:int = 80):
    db_clubs = db.query(Clubs).filter(Clubs.show == True).all()
    if not db_clubs:
        raise HTTPException(status_code=204, detail="Can't find players of club")
    result = []
    # get manager's full name from manager's id
    for club in db_clubs:
        ratio = fuzz.partial_ratio(club.club_name.lower(), search_name.lower())
        if ratio < threshold:
            continue
        
        manager_full_name = db.query(Users).filter(Users.user_id == club.manager).first().full_name
        if not manager_full_name:
            raise HTTPException(status_code=204, detail= f"Can't find manager of club: {club.club_name}")
        club_data = {
            "club_name": club.club_name,
            "club_shortname": club.club_shortname,
            "total_player": club.total_player,
            "nation": club.nation,
            "manager": manager_full_name
        }
        result.append(club_data)
    
    if len(result) == 0:
        return {
            "message":f"No clubs match the name: {search_name}"
        }

    return result


@route.post("/create-club")
async def create_club(db: db_deps, current_user : CurrentUser, new_club: Club_Create):
    hasPermission = check_is_manager(db, current_user)

    return crud_create_club(db, current_user, new_club)



