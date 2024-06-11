from fastapi import APIRouter, HTTPException
from sqlalchemy import func, or_

from api.deps import CurrentUser
from core.db import db_deps, Depends
from schemas.db import Clubs, Users, Matches, Stadiums
from schemas.stadiums import StadiumAdd, List
from fuzzywuzzy import fuzz

from utils import (
    is_admin,
    check_event_time,
)

route = APIRouter()

@route.get('/get-all-stadiums')
async def get_all_stadiums(db: db_deps):
    query = db.query(Stadiums).filter(Stadiums.show == True).all()
    
    return query

@route.get("/test")
async def test(s1:str, s2:str):
    return fuzz.partial_ratio(str(s1).lower(), str(s2).lower())

@route.post("/add-stadium")
async def add_stadium(db:db_deps, current_user: CurrentUser, new:StadiumAdd):
    # check permission
    is_admin(db, current_user)

    # check duplicate stadium name
    stadiums = db.query(Stadiums).all()
    dup = None
    for s in stadiums:
        ratio = fuzz.partial_ratio(str(s.std_name), str(new.std_name))
        if ratio >= 100:
            dup = s
            break
        
    if dup and dup.show == True:
        raise HTTPException(status_code=400, detail="Duplicated stadium name")
    elif dup and dup.show == False:
        dup.cap = new.cap
        dup.show = True
        db.commit()
        db.refresh(dup)
        return dup
    # no dup -> add 
    max_id = db.query(func.max(Stadiums.std_id)).scalar()
    new_db_std = Stadiums(
        std_id = (max_id or 0) + 1,
        std_name = new.std_name,
        cap = new.cap,
        show = True
    )
    db.add(new_db_std)
    db.commit()
    db.refresh(new_db_std)
    return new_db_std

@route.put("/delete-stadium")
async def delete_stadium(db: db_deps, current_user: CurrentUser, std_id : int):
    #check permission
    is_admin(db, current_user)

    # find the target std
    target = db.query(Stadiums).filter(Stadiums.show ==True, Stadiums.std_id == std_id).first()

    if not target:
        raise HTTPException(status_code=400, detail="Can't find stadium")

    # found -> check any matches on this std
    match = db.query(Matches).filter(Matches.show==True, Matches.stadium==target.std_id).first()
    if match:
        raise HTTPException(status_code=405, detail="Can't delete this stadium, there'")

    # No conflict -> delete

    target.show=False

    db.commit()
    return target

@route.get('/get-deleted-stadiums')
async def get_deleted_stadiums(db: db_deps):
    query = db.query(Stadiums).filter(Stadiums.show == False).all()

    return query

@route.put("/restor-stadium")
async def restore_stadium(db:db_deps, current_user:CurrentUser, std_int:int):
    #check permission
    is_admin(db, current_user)

    #find target
    target = db.query(Stadiums).filter(Stadiums.show==False, Stadiums.std_id==std_id).first()

    if not target:
        raise HTTPException(status_code=400, detail="Can't find stadium")

    # restore
    target.show=True
    db.commit()
    return target

@route.get("/matches-of-stadium")
async def get_matches_of_stadium(db:db_deps, std_id:int):
    # find matches
    matches = db.query(Matches).filter(Matches.show==True, Matches.stadium==std_id).all()
    
    return matches


    