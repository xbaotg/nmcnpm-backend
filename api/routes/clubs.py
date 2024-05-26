from datetime import date

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func

from api.deps import CurrentUser, List
from core.db import db as code_db
from core.db import db_deps
from schemas.db import Clubs, Players, Users
from schemas.players import ClubCreate, ClubShow, ClubUpdate

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


@route.post("/add_clubs")
async def add_clubs(club: ClubCreate, db: db_deps):  # current_user: CurrentUser):
    try:
        # hasPermission = get_user_permission(current_user, db, "manager")
        newDict = club.dict()
        for key, value in newDict.items():
            if value == "string":
                return {"message": f"{key} is required."}

        count = db.query(func.max(Clubs.club_id)).scalar()
        newDict["club_id"] = (count or 0) + 1
        new_db_club = Clubs(**newDict)

        db.add(new_db_club)
        db.commit()
        db.refresh(new_db_club)
        return new_db_club

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    
@route.get("/get_clubs_by_name", response_model=List[ClubShow])
async def get_clubs_by_name(club_name: str, db: db_deps, threshold: int = 80):
    try:
        clubs = db.query(Clubs).filter(Clubs.show == True).all()
        matched_clubs = [
            club
            for club in clubs
            if fuzz.partial_ratio(club.club_name.lower(), club_name.lower())
            >= threshold
        ]

        if not matched_clubs:
            raise HTTPException(status_code=204, detail="Cannot find clubs")

        return matched_clubs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    

@route.put("/update_club")
async def update_club(
    club_id: int, club_update: ClubUpdate, db: db_deps):  # current_user: CurrentUser):
    try:
        # hasPermission = get_user_permission(current_user, db, "manager")
        target = db.query(Clubs).filter(Clubs.club_id == club_id).first()
        update_info = club_update.dict(exclude_unset=True)
        for key, value in update_info.items():
            if value == "string":
                return {"message": f"{key} is required."}
            
            setattr(target, key, value)
        db.commit()
        db.refresh(target)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}!")
    return target
