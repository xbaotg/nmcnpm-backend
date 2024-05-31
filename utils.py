from datetime import date, datetime, time, timedelta
from fastapi import HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import select, exists, or_, func

from core.db import db_deps, get_params, db
from api.deps import CurrentUser

from schemas.db import Users, Params, Players, Clubs, Referees, Matches
from schemas.params import Show_Params
from schemas.matches import AddMatch

def is_admin(db: db_deps, current_user: CurrentUser):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    # check permission of user_role
    if user_role != "admin":
        raise HTTPException(
            status_code=401, detail="You don't have permission to do this action!"
        )

    return True

params = get_params(Params, db)
#default values
MIN_PLAYER_AGE = 16
MAX_PLAYER_AGE = 40
MIN_CLUB_PLAYER = 2
MAX_CLUB_PLAYER = 22
MAX_FOREIGN_PLAYER = 3
POINTS_WIN = 2
POINTS_DRAW = 1
POINTS_LOSE = 0
MAX_GOAL_TYPES = 3
MAX_GOAL_TIME = "01:30:00"

# overwrite to use when update params, checking conflict data with new MIN/MAX age
def is_valid_age(bday: date, db: db = db, MIN: int = 16, MAX: int = 40, overwrite: bool = False):
    if not overwrite:
        params = get_params(Params, db)
        MIN_PLAYER_AGE = params.min_player_age
        MAX_PLAYER_AGE = params.max_player_age
    else:
        MIN_PLAYER_AGE = MIN
        MAX_PLAYER_AGE = MAX
    
    now = date.today()
    age = now.year - bday.year - ((now.month, now.day) < (bday.month, bday.day))
    print("age = ", age)
    print("min age: ", MIN_PLAYER_AGE)
    if age < MIN_PLAYER_AGE or age > MAX_PLAYER_AGE:
        return False

    return True

def get_user_role(db: db_deps, current_user: CurrentUser):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    return user_role

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

def check_owner(db: db_deps, current_user: CurrentUser, club_id: int):
    club = db.query(Clubs).filter(Clubs.club_id == club_id).first()
    if club is None:
        return None
    if (current_user['user_id'] == club.manager):
        return True

    return False

# Use when add or delete a player from club
def check_club_player_num(db: db_deps, total_player: int):
    params = get_params(Params, db)
    MIN_CLUB_PLAYER = params.min_club_player
    MAX_CLUB_PLAYER = params.max_club_player
    if total_player < MIN_CLUB_PLAYER or total_player > MAX_CLUB_PLAYER:
        return False
    return True

# Use when add a player to a club 
def check_foreign_player(db: db_deps, count: int):
    params = get_params(Params, db)
    MAX_FOREIGN_PLAYER = params.max_foreign_player

    if (count <= MAX_FOREIGN_PLAYER):
        return True, MAX_FOREIGN_PLAYER
    else:
        return False, MAX_FOREIGN_PLAYER

def auto_count_total_player(db: db_deps, club_id: int):
    count = db.query(Players).filter(Players.show == True, Players.player_club == club_id).count()

    target = db.query(Clubs).filter(Clubs.show == True, Clubs.club_id == club_id).first()
    if not target:
        raise HTTPException(status_code=204, detail="Can't find any clubs")
    
    target.total_player = count
    db.commit()
    return count 

# def auto_count_goal_types(db: db_deps)

def is_int(var: str):
    try:
        var = int(var)
        return True
    except ValueError:
        return False

def convert_from_attr(model, value, src_field, res_field, from_name : bool = False):
    if from_name:
        records = db.query(model).filter(
            getattr(model, "show") == True
        ).all()
        res = None
        ratio = 90
        for record in records:
            current_ratio = (fuzz.partial_ratio(str(getattr(record, src_field)).lower(), value.lower()))
            # print(getattr(record, src_field), end=": ")
            # print(current_ratio)
            if current_ratio > ratio:
                res = record
                ratio = current_ratio

        if res:
            res = getattr(res, res_field)
            return res
        return None
    else: 
        res = db.query(model).filter(getattr(model, "show") == True, getattr(model, src_field) == value).first()
        if res:
            res = getattr(res, res_field)
            return res
        return None

def valid_add_match(db: db_deps, match: AddMatch): # return a basemodel with all values are IDs
    # convert team1 , team2 (name to id)
    team1 = None
    team2 = None
    if not is_int(match.team1):
        team1 = convert_from_attr(Clubs, match.team1, "club_name", "club_id", True)
    else:
        team1 = int(match.team1)
        target = db.query(Clubs).filter(Clubs.club_id == team1, Clubs.show == True).first()
        if not target:
            raise HTTPException(status_code=400, detail = f"Invalid team1")

    if not is_int(match.team2):
        team2 = convert_from_attr(Clubs, match.team2, "club_name", "club_id", True)
    else:
        team2 = int(match.team2)
        target = db.query(Clubs).filter(Clubs.club_id == team2, Clubs.show == True).first()
        if not target:
            raise HTTPException(status_code=400, detail = f"Invalid team2")
        

    print(f"check {team1}, {team2}")
    if (not team1 ) or (not team2) or (team1 == team2):
        raise HTTPException(status_code=400, detail="Invalid host team or away team")


    
    # check start time
        # convert string to datetime
    start_time = datetime.strptime(match.start, f"%H:%M %d/%m/%Y")

        # check overlap between matches (1 team play 1 match per day)
    overlap = db.query(Matches).filter(
        Matches.show == True,
        func.date(Matches.start) == start_time.date(),
        or_(Matches.team1 == team1),
        or_(Matches.team2 == team1),
        or_(Matches.team1 == team2),
        or_(Matches.team2 == team2)
    ).first()
    if (overlap):
        raise HTTPException(status_code=400, detail="A team can only play 1 match per day !")

        # check today <= start_time
    current = datetime.now()
    if (current.date() >= start_time.date()):
        raise HTTPException(status_code=400, detail= f"Invalid match start time: start on {start_time.date()} but today is {current.date()}")
        return {"message": "Invalid match start time !"}

    # check valid refs
        # convert name to id
    ref = None 
    var = None 
    lineman = None
    if not is_int(match.ref):
        ref = convert_from_attr(Referees, match.ref, "ref_name", "ref_id", True)
    else:
        ref = int(match.ref)
        target = db.query(Referees).filter(Referees.show == True, Referees.ref_id == ref).first()
        if not target:
            raise HTTPException(status_code=400, detail = f"Referee not found !")

    if not is_int(match.var):
        var = convert_from_attr(Referees, match.var, "ref_name", "ref_id", True)
    else:
        var = int(match.var)
        target = db.query(Referees).filter(Referees.show == True, Referees.ref_id == var).first()
        if not target:
            raise HTTPException(status_code=400, detail = f"Var referee not found !")

    if not is_int(match.lineman):
        lineman = convert_from_attr(Referees, match.lineman, "ref_name", "ref_id", True)
    else:
        lineman = int(match.lineman)
        target = db.query(Referees).filter(Referees.show == True, Referees.ref_id == lineman).first()
        if not target:
            raise HTTPException(status_code=400, detail = f"Lineman referee not found !")
    
    match.team1 = team1   
    match.team2 = team2   
    match.ref = ref   
    match.var = var   
    match.lineman = lineman   
    return match


