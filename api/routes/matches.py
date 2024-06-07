from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Matches, Referees
from schemas.matches import AddMatch, MatchResponse, MatchUpdate

from utils import (
    valid_add_match,
    valid_update_match,
    is_int,
    convert_from_attr,
    is_admin,
    count_goals,
)

route = APIRouter()


@route.get("/get-matches")
async def get_matches(db: db_deps):
    db_matches = db.query(Matches).filter(Matches.show == True).all()
    res_list = []
    for match in db_matches:
        now = datetime.now()
        if now > match.start:
            goal1, goal2 = count_goals(db, match.match_id)
        else:
            goal1 = match.goal1
            goal2 = match.goal2
        res = MatchResponse(
            match_id=match.match_id,
            team1=convert_from_attr(Clubs, match.team1, "club_id", "club_name"),
            team2=convert_from_attr(Clubs, match.team2, "club_id", "club_name"),
            start=str(match.start.strftime(f"%H:%M %d/%m/%Y")),
            goal1=goal1,
            goal2=goal2,
            ref=convert_from_attr(Referees, match.ref_id, "ref_id", "ref_name"),
            var=convert_from_attr(Referees, match.var_id, "ref_id", "ref_name"),
            lineman=convert_from_attr(Referees, match.lineman_id, "ref_id", "ref_name"),
        )
        res_list.append(res)
    return res_list


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
            team1=convert_from_attr(Clubs, match.team1, "club_id", "club_name"),
            team2=convert_from_attr(Clubs, match.team2, "club_id", "club_name"),
            start=str(match.start.strftime(f"%H:%M %d/%m/%Y")),
            goal1=match.goal1,
            goal2=match.goal2,
            ref=convert_from_attr(Referees, match.ref_id, "ref_id", "ref_name"),
            var=convert_from_attr(Referees, match.var_id, "ref_id", "ref_name"),
            lineman=convert_from_attr(Referees, match.lineman_id, "ref_id", "ref_name"),
        )
        res_list.append(res)
    return res_list


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
            team1=convert_from_attr(Clubs, match.team1, "club_id", "club_name"),
            team2=convert_from_attr(Clubs, match.team2, "club_id", "club_name"),
            start=str(match.start.strftime(f"%H:%M %d/%m/%Y")),
            goal1=match.goal1,
            goal2=match.goal2,
            ref=convert_from_attr(Referees, match.ref_id, "ref_id", "ref_name"),
            var=convert_from_attr(Referees, match.var_id, "ref_id", "ref_name"),
            lineman=convert_from_attr(Referees, match.lineman_id, "ref_id", "ref_name"),
        )
        res_list.append(res)
    return res_list


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
            team1=convert_from_attr(Clubs, match.team1, "club_id", "club_name"),
            team2=convert_from_attr(Clubs, match.team2, "club_id", "club_name"),
            start=str(match.start.strftime(f"%H:%M %d/%m/%Y")),
            goal1=match.goal1,
            goal2=match.goal2,
            ref=convert_from_attr(Referees, match.ref_id, "ref_id", "ref_name"),
            var=convert_from_attr(Referees, match.var_id, "ref_id", "ref_name"),
            lineman=convert_from_attr(Referees, match.lineman_id, "ref_id", "ref_name"),
        )
        res_list.append(res)
    return res_list


# ADD MATCH: can handle string input or id input
@route.post("/add-match")
async def add_match(db: db_deps, current_user: CurrentUser, match: AddMatch):
    is_admin(db, current_user)
    match_return = valid_add_match(
        db, match
    )  # check valid data and convert values from string into IDs
    db_match = match_return

    # auto complete goal1, goal2 and show
    max_id = db.query(func.max(Matches.match_id)).scalar()
    new_match = Matches(
        match_id=(max_id or 0) + 1,
        team1=db_match.team1,
        team2=db_match.team2,
        start=datetime.strptime(db_match.start, f"%H:%M %d/%m/%Y"),
        goal1=None,
        goal2=None,
        ref_id=db_match.ref,
        var_id=db_match.var,
        lineman_id=db_match.lineman,
        show=True,
    )

    # result for user
    match_return.team1 = convert_from_attr(
        Clubs, match_return.team1, "club_id", "club_name"
    )
    match_return.team2 = convert_from_attr(
        Clubs, match_return.team2, "club_id", "club_name"
    )
    match_return.ref = convert_from_attr(
        Referees, match_return.ref, "ref_id", "ref_name"
    )
    match_return.var = convert_from_attr(
        Referees, match_return.var, "ref_id", "ref_name"
    )
    match_return.lineman = convert_from_attr(
        Referees, match_return.lineman, "ref_id", "ref_name"
    )

    db.add(new_match)
    db.commit()
    db.refresh(new_match)

    return match_return, new_match


#     # Chuỗi thời gian
# time_string = "01:12 31/05/2024"

# # Chuyển đổi chuỗi thành datetime
# start_time = datetime.strptime(time_string, f"%H:%M %d/%m/%Y")


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
        raise HTTPException(status_code=400, detail=f"Can't find any match")

    # check if the input is valid
    update = valid_update_match(db, update, id)

    # update
    try:
        today = datetime.now()
        start_time = datetime.strptime(update.start, f"%H:%M %d/%m/%Y")

        if update.goal1 != -1 and update.goal2 != -1:
            # update goal -> no update time -> check today >= update.start
            if not (today >= start_time):
                raise HTTPException(
                    status_code=400,
                    detail=f"Can't update result for unfinished matches !",
                )

            target.goal1 = update.goal1
            target.goal2 = update.goal2

        else:
            # no goal update -> update other attributes -> check today < update.start
            if today.date() >= start_time.date():
                raise HTTPException(
                    status_code=400,
                    detail=f"Today is {today.strftime(f'%H:%M %d/%m/%Y')}, but match start at {start_time.strftime(f'%H:%M %d/%m/%Y')}",
                )

            target.start = start_time
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

    return target


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
    today = datetime.now()
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

    return target


# DELETE
@route.put("/delete-match")
async def delete_match(db: db_deps, current_user: CurrentUser, id: int):
    is_admin(db, current_user)
    target = (
        db.query(Matches).filter(Matches.show == True, Matches.match_id == id).first()
    )

    if not target:
        return {"message": "Can't find any matches, maybe deleted"}

    target.show = False

    db.commit()
    db.refresh(target)

    return {"message": "Delete match successfully (temporarily)!"}


# delete permanently
@route.delete("/permanently-delete-match")
async def permanently_delete_match(db: db_deps, current_user: CurrentUser, id: int):
    is_admin(db, current_user)
    target = (
        db.query(Matches).filter(Matches.show == False, Matches.match_id == id).first()
    )

    if not target:
        return {
            "message": "Can't find any matches, make sure to temporarily delete first "
        }

    db.delete(target)
    db.commit()
    db.refresh(target)

    return {"message": "Delete match successfully !"}
