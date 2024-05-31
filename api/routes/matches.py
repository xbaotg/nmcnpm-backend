from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Matches, Referees
from schemas.matches import AddMatch,MatchResponse

from utils import valid_add_match, is_int, convert_from_attr, is_admin

route = APIRouter()



@route.get("/test")
async def test(db:db_deps, value : str):
    res = convert_from_attr(Clubs, value, "club_name", "club_shortname", True)
    return res

@route.get("/get-matches")
async def get_matches(db: db_deps):
    db_matches = db.query(Matches).filter(Matches.show == True).all()
    res_list = []
    for match in db_matches:
        res = MatchResponse(
            team1 = convert_from_attr(Clubs, match.team1, "club_id", "club_name"),
            team2 = convert_from_attr(Clubs, match.team2, "club_id", "club_name"),
            start = str(match.start.strftime(f"%H:%M %d/%m/%Y")),
            goal1 = match.goal1,
            goal2 = match.goal2,
            ref = convert_from_attr(Referees, match.ref_id, "ref_id", "ref_name"),
            var = convert_from_attr(Referees, match.var_id, "ref_id", "ref_name"),
            lineman = convert_from_attr(Referees, match.lineman_id, "ref_id", "ref_name")
        )
        res_list.append(res)
    return res_list


# ADD MATCH: can handle string input or id input
@route.post("/add-match")
async def add_match(db:db_deps, current_user: CurrentUser, match : AddMatch):
    is_admin(db, current_user)
    match_return = valid_add_match(db, match) # check valid data and convert values from string into IDs
    db_match = match_return

    # auto complete goal1, goal2 and show
    max_id = db.query(func.max(Matches.match_id)).scalar()
    new_match = Matches(
        match_id = (max_id or 0) + 1,
        team1 = db_match.team1,
        team2 = db_match.team2,
        start = datetime.strptime(db_match.start, f"%H:%M %d/%m/%Y"),
        goal1 = None,
        goal2 = None,
        ref_id = db_match.ref,
        var_id = db_match.var,
        lineman_id = db_match.lineman,
        show = True
    )

    # result for user 
    match_return.team1 = convert_from_attr(Clubs, match_return.team1, "club_id", "club_name")
    match_return.team2 = convert_from_attr(Clubs, match_return.team2, "club_id", "club_name")
    match_return.ref = convert_from_attr(Referees, match_return.ref, "ref_id", "ref_name")
    match_return.var = convert_from_attr(Referees, match_return.var, "ref_id", "ref_name")
    match_return.lineman = convert_from_attr(Referees, match_return.lineman, "ref_id", "ref_name")

    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    
    return match_return, new_match


#     # Chuỗi thời gian
# time_string = "01:12 31/05/2024"

# # Chuyển đổi chuỗi thành datetime
# start_time = datetime.strptime(time_string, f"%H:%M %d/%m/%Y")


