from datetime import date
from sqlalchemy import func

from core.db import db_deps
from fastapi import APIRouter, HTTPException, Depends
from schemas.db import Clubs, Users, Players
from schemas.clubs import Club_Response, Club_Create, Club_Update
from schemas.players import PlayerShow
from crud import create_club as crud_create_club

from api.deps import List, CurrentUser, get_password_hash, fuzz
from utils import check_owner, check_is_manager, get_user_role

route = APIRouter()


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
    

@route.get("/search-club-by-name", response_model=List[Club_Response] | dict)
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

@route.get("/get-players-of-clubs/{club_id}", response_model=List[PlayerShow]|dict)
async def get_all_players_of_clubs(db: db_deps, club_id: int):
    db_players = db.query(Players).filter(Players.player_club == club_id).all()
    if db_players:
        return db_players
    else:
        raise HTTPException(
            status_code=204,
            detail = f"Can't find any players of club with id {club_id} !"
        )

@route.post("/create-club")
async def create_club(db: db_deps, current_user : CurrentUser, new_club: Club_Create):
    hasPermission = check_is_manager(db, current_user)

    return crud_create_club(db, current_user, new_club)



@route.put("/update-club/{club_id}", response_model=Club_Update|dict)
async def update_club(db: db_deps, current_user: CurrentUser, club_id: int, new_info: Club_Update):
    print("Start")   
    user_role = get_user_role(db, current_user)
    print("Check")
    is_owner = check_owner(db,current_user,club_id)
    print("Done")
    if is_owner is None:
        raise HTTPException(status_code=204, detail=f"Can't find the club with ID {club_id} !")
    if not is_owner and user_role == "manager":
        return {"message": "You are not the owner of this club"}
    
    try:
       target = db.query(Clubs).filter(Clubs.club_id == club_id).first()
       update_info = new_info.dict(exclude_unset=True)
       for key, value in update_info.items():  #
           if value == "string":
               continue
           if key == "manager" and value == 0:
               continue
           setattr(target, key, value)
       db.commit()
       db.refresh(target)
       return target
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}!")


