from fastapi import APIRouter, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends
from fuzzywuzzy import fuzz

from api.deps import CurrentUser
from core.db import db_deps
from schemas.db import Clubs, Users, Matches, Stadiums
from schemas.stadiums import StadiumAdd, List
from utils import (
    is_admin,
    check_event_time,
)

route = APIRouter()


def create_error_response(message: str):
    return {"status": "error", "message": message}


def create_success_response(message: str, data=None):
    return {"status": "success", "message": message, "data": data}


@route.get("/get-all-stadiums")
async def get_all_stadiums(db: db_deps):
    query = db.query(Stadiums).filter(Stadiums.show == True).all()
    return create_success_response("Stadiums fetched successfully", query)


@route.post("/add-stadium")
async def add_stadium(
    db: db_deps,
    current_user: CurrentUser,
    new: StadiumAdd,
):
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
        raise HTTPException(
            status_code=400, detail=create_error_response("Duplicated stadium name")
        )
    elif dup and dup.show == False:
        dup.cap = new.cap
        dup.show = True
        db.commit()
        db.refresh(dup)
        return create_success_response("Stadium restored successfully", dup)

    # no dup -> add
    max_id = db.query(func.max(Stadiums.std_id)).scalar()
    new_db_std = Stadiums(
        std_id=(max_id or 0) + 1, std_name=new.std_name, cap=new.cap, show=True
    )
    db.add(new_db_std)
    db.commit()
    db.refresh(new_db_std)
    return create_success_response("Stadium added successfully", new_db_std)


@route.put("/delete-stadium")
async def delete_stadium(
    db: db_deps,
    current_user: CurrentUser,
    std_id: int,
):
    # check permission
    is_admin(db, current_user)

    # find the target std
    target = (
        db.query(Stadiums)
        .filter(Stadiums.show == True, Stadiums.std_id == std_id)
        .first()
    )

    if not target:
        raise HTTPException(
            status_code=400, detail=create_error_response("Can't find stadium")
        )

    # found -> check any matches on this std
    match = (
        db.query(Matches)
        .filter(Matches.show == True, Matches.stadium == target.std_id)
        .first()
    )
    if match:
        raise HTTPException(
            status_code=405,
            detail=create_error_response(
                "Can't delete this stadium, there's a match scheduled"
            ),
        )

    # No conflict -> delete
    target.show = False
    db.commit()
    return create_success_response("Stadium deleted successfully", target)


@route.get("/get-deleted-stadiums")
async def get_deleted_stadiums(db: db_deps):
    query = db.query(Stadiums).filter(Stadiums.show == False).all()
    return create_success_response("Deleted stadiums fetched successfully", query)


@route.put("/restore-stadium")
async def restore_stadium(
    db: db_deps,
    current_user: CurrentUser,
    std_id: int,
):
    # check permission
    is_admin(db, current_user)

    # find target
    target = (
        db.query(Stadiums)
        .filter(Stadiums.show == False, Stadiums.std_id == std_id)
        .first()
    )

    if not target:
        raise HTTPException(
            status_code=400, detail=create_error_response("Can't find stadium")
        )

    # restore
    target.show = True
    db.commit()
    return create_success_response("Stadium restored successfully", target)


@route.get("/matches-of-stadium")
async def get_matches_of_stadium(db: db_deps, std_id: int):
    # find matches
    matches = (
        db.query(Matches).filter(Matches.show == True, Matches.stadium == std_id).all()
    )
    return create_success_response("Matches fetched successfully", matches)
