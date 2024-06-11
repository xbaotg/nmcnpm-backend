from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_
from starlette.responses import JSONResponse

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Matches, Referees
from schemas.matches import AddMatch, MatchResponse, MatchUpdate

from loguru import logger

from utils import (
    datetime_to_unix,
    unix_to_datetime,
    valid_add_match,
    valid_update_match,
    is_int,
    convert_from_attr,
    is_admin,
    count_goals,
)

app = FastAPI()
route = APIRouter()


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail},
    )


@route.get("/get-matches")
async def get_matches(db: db_deps):
    db_matches = db.query(Matches).filter(Matches.show == True).all()
    res_list = []

    for match in db_matches:
        now = datetime.now()
        now_unix = now.timestamp()

        res = MatchResponse(
            match_id=match.match_id,
            team1=match.team1,
            team2=match.team2,
            start=match.start,
            finish=match.finish,
            goal1=match.goal1,
            goal2=match.goal2,
            ref=match.ref_id,
            var=match.var_id,
            lineman=match.lineman_id,
        )

        res_list.append(res)

    return {
        "status": "success",
        "message": "Matches retrieved successfully",
        "data": res_list,
    }


@route.get("/filter-matches-by-team-name")
async def get_matches(db: db_deps, club: str):
    search = convert_from_attr(Clubs, club, "club_name", "club_id", True)

    db_matches = (
        db.query(Matches)
        .filter(
            Matches.show == True, or_(Matches.team1 == search, Matches.team2 == search)
        )
        .all()
    )

    res_list = []
    for match in db_matches:
        res = MatchResponse(
            match_id=match.match_id,
            team1=match.team1,
            team2=match.team2,
            start=match.start,
            finish=match.finish,
            goal1=match.goal1,
            goal2=match.goal2,
            ref=match.ref_id,
            var=match.var_id,
            lineman=match.lineman_id,
        )
        res_list.append(res)
    return {
        "status": "success",
        "message": "Matches filtered by team name successfully",
        "data": res_list,
    }


# get unfinished matches
@route.get("/fixtures")
async def get_fixtures(db: db_deps):
    db_matches = (
        db.query(Matches).filter(Matches.show == True, Matches.goal1 == None).all()
    )

    res_list = []
    for match in db_matches:
        res = MatchResponse(
            match_id=match.match_id,
            team1=match.team1,
            team2=match.team2,
            start=match.start,
            finish=match.finish,
            goal1=match.goal1,
            goal2=match.goal2,
            ref=match.ref_id,
            var=match.var_id,
            lineman=match.lineman_id,
        )
        res_list.append(res)
    return {
        "status": "success",
        "message": "Fixtures retrieved successfully",
        "data": res_list,
    }


# get result = get finished matches
@route.get("/results")
async def get_matches_results(db: db_deps):
    db_matches = (
        db.query(Matches).filter(Matches.show == True, Matches.goal1 != None).all()
    )

    res_list = []
    for match in db_matches:
        res = MatchResponse(
            match_id=match.match_id,
            team1=match.team1,
            team2=match.team2,
            start=match.start,
            finish=match.finish,
            goal1=match.goal1,
            goal2=match.goal2,
            ref=match.ref_id,
            var=match.var_id,
            lineman=match.lineman_id,
        )
        res_list.append(res)

    return {
        "status": "success",
        "message": "Match results retrieved successfully",
        "data": res_list,
    }


# ADD MATCH: can handle string input or id input
@route.post("/add-match")
async def add_match(db: db_deps, current_user: CurrentUser, match: AddMatch):
    is_admin(db, current_user)

    match_return = valid_add_match(
        db, match
    )  # check valid data and convert values from string into IDs

    db_match = match_return

    # scale down start and finish time
    db_match.start = min(db_match.start, 2 * 10**9)
    db_match.finish = min(db_match.finish, 2 * 10**9)

    # auto complete goal1, goal2 and show
    max_id = db.query(func.max(Matches.match_id)).scalar()
    new_match = Matches(
        match_id=(max_id or 0) + 1,
        team1=db_match.team1,
        team2=db_match.team2,
        start=db_match.start,
        finish=db_match.finish,
        goal1=db_match.goal1,
        goal2=db_match.goal2,
        ref_id=db_match.ref,
        var_id=db_match.var,
        lineman_id=db_match.lineman,
        show=True,
    )

    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    return {
        "status": "success",
        "message": "Match added successfully",
        "data": new_match,
    }


@route.put("/update-match")
async def update_match(
    db: db_deps, current_user: CurrentUser, update: MatchUpdate, id: int
):
    is_admin(db, current_user)

    # search for the match user want to udpate
    target = (
        db.query(Matches)
        .filter(
            Matches.show == True,
            Matches.match_id == id,
        )
        .first()
    )

    if not target:
        raise HTTPException(status_code=400, detail="Can't find any match")

    # check if the input is valid
    update = valid_update_match(db, update, id)

    try:
        today = datetime_to_unix(datetime.now())
        start_time = update.start

        target.start = start_time
        target.finish = update.finish
        target.team1 = update.team1
        target.team2 = update.team2
        target.ref_id = update.ref
        target.var_id = update.var
        target.lineman_id = update.lineman

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

    try:
        db.commit()
        db.refresh(target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    return {
        "status": "success",
        "message": "Match updated successfully",
        "data": target,
    }


@route.put("/update-result")
async def update_result(
    db: db_deps, current_user: CurrentUser, id: int, goal1: int, goal2: int
):
    is_admin(db, current_user)

    target = (
        db.query(Matches).filter(Matches.match_id == id, Matches.show == True).first()
    )

    if not target:
        raise HTTPException(status_code=400, detail="Can't find any matches!")

    # check if match has finished
    today = datetime_to_unix(datetime.now())
    if today < target.start:
        raise HTTPException(
            status_code=400, detail="Can't update result for unfinished matches!"
        )

    if goal1 < 0 or goal2 < 0:
        goal1 = None
        goal2 = None
    # update
    target.goal1 = goal1
    target.goal2 = goal2

    db.commit()
    db.refresh(target)

    return {
        "status": "success",
        "message": "Result updated successfully",
        "data": target,
    }


# DELETE
@route.put("/delete-match")
async def delete_match(db: db_deps, current_user: CurrentUser, id: int):
    is_admin(db, current_user)
    target = (
        db.query(Matches).filter(Matches.show == True, Matches.match_id == id).first()
    )

    if not target:
        return {"status": "error", "message": "Can't find any matches, maybe deleted"}

    target.show = False

    db.commit()
    db.refresh(target)

    return {
        "status": "success",
        "message": "Match deleted successfully (temporarily)",
        "data": target,
    }


# delete permanently
@route.delete("/permanently-delete-match")
async def permanently_delete_match(db: db_deps, current_user: CurrentUser, id: int):
    is_admin(db, current_user)
    target = (
        db.query(Matches).filter(Matches.show == False, Matches.match_id == id).first()
    )

    if not target:
        return {
            "status": "error",
            "message": "Can't find any matches, make sure to temporarily delete first ",
        }

    db.delete(target)
    db.commit()
    db.refresh(target)

    return {
        "status": "success",
        "message": "Match permanently deleted successfully",
        "data": target,
    }


app.include_router(route)
