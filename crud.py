from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import func
from core.db import db, db_deps
from schemas.db import Users, Clubs, Players
from core.security import verify_password, get_password_hash
from api.deps import CurrentUser, Annotated, List
from schemas.users import UserCreateBase, UserReg
from schemas.clubs import Club_Create
from utils import is_valid_age, check_club_player_num, check_foreign_player

from schemas.players import Player_Add_With_Club


def authenticate_user(username: str, password: str, db: db_deps):
    try:
        user = db.query(Users).filter(Users.user_name == username).first()
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"The error is : {str(e)}")

    if not user:
        return False

    try:
        if not verify_password(password, user.password):
            return False

    except Exception:
        if user.password != password:
            return False

    return user


def create_user(db: db_deps, new_user: UserCreateBase) -> Users | dict:
    newUserdict = new_user.dict()
    # check duplicated user_name
    duplicated_name = (
        db.query(Users).filter(Users.user_name == newUserdict["user_name"]).first()
    )
    if duplicated_name is not None:
        return {
            "message": f"{newUserdict['user_name']} has been used, please choose another user name !"
        }

    for key, value in newUserdict.items():
        if value == "string":  # kiem tra noi dung khong duoc nhap
            return {"message": f"{key} is required."}

        if key == "user_bday":  # kiem tra tuoi
            if not is_valid_age(value):
                return {"message": "User age is not legal"}

    # auto complete data
    if newUserdict["role"] != "admin" and newUserdict["role"] != "manager":
        raise HTTPException(
            status_code=401, detail="Role must be 'admin' or 'manager'!"
        )

    newUserdict["password"] = get_password_hash(newUserdict["password"])
    newUserdict["show"] = True
    newUserdict["user_id"] = 1 + (db.query(func.max(Users.user_id)).scalar() or 0)

    try:
        new_db_user = Users(**newUserdict)
        db.add(new_db_user)
        db.commit()

        return {"message": "Added user succesfully !"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Can't add new user: {str(e)}")


def get_info_user(db: db_deps, current_user: CurrentUser):
    try:
        user = (
            db.query(Users).filter(Users.user_name == current_user["user_name"]).first()
        )

        if user is None:
            raise HTTPException(status_code=204, detail="Can't find user !")

        # bday = datetime.combine(user.user_bday, datetime.min.time())
        res = UserReg(
            user_id=user.user_id,
            full_name=user.full_name,
            role=user.role,
            user_name=user.user_name,
            user_mail=user.user_mail,
            user_nation=user.user_nation,
            user_bday=user.user_bday,
            show=user.show,
        )
        return res

    except HTTPException as e:
        raise

    except Exception as e:
        import traceback

        traceback.print_exc()

        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def create_club(
    db: db_deps, current_user: CurrentUser, new_club: Club_Create
) -> Clubs | dict:

    new_club = new_club.dict()

    # check duplicated club_name:
    duplicated_name = (
        db.query(Clubs).filter(Clubs.club_name == new_club["club_name"]).first()
    )
    if duplicated_name is not None:
        return {
            "message": f"{new_club['club_name']} has been used, please choose another club name !"
        }

    # check if current_user is another club's manager
    duplicated_manager = (
        db.query(Clubs)
        .filter(Clubs.manager == current_user["user_id"], Clubs.show == True)
        .first()
    )
    if duplicated_manager is not None:
        return {"message": f"You can just create 1 club!"}

    # check not entered values
    for key, value in new_club.items():
        if key == "club_players":
            continue
        if value == "string":
            return {"message": f"{key} is required."}

    # auto complete data
    count = db.query(func.max(Clubs.club_id)).scalar()
    new_club["club_id"] = (count or 1) + 1
    new_club["manager"] = current_user["user_id"]
    new_club["show"] = True

    # extract club's players info
    club_players = new_club.pop("club_players")

    # check player num
    if not check_club_player_num(db, len(club_players)):
        db.rollback()
        return {"message": "Club doesn't have enough players"}

    # check maximum foreign player
    count = 0
    for player in club_players:
        if player.palyer_nation != "VIE":
            count += 1
    valid, max_foreign_player = check_foreign_player(db, count)
    if not valid:
        return {
            "message": f"Too many foreign players (maximum is {max_foreign_player})"
        }

    # add total players
    new_club["total_player"] = len(club_players)

    # commit to database
    try:
        new_db_club = Clubs(**new_club)
        db.add(new_db_club)
        db.commit()
        return {"message": "Created club successfully!"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Internal Server Error: Can't create new club"
        )

    # add player
    iter = 0
    try:
        for player in club_players:
            # Kiểm tra cầu thủ trùng lặp
            dup_player = (
                db.query(Players)
                .filter(Players.player_name == player["player_name"])
                .first()
            )
            if dup_player is not None:
                if (
                    dup_player.player_bday == player["player_bday"]
                    and dup_player.player_nation == player["player_nation"]
                    and dup_player.player_pos == player["player_pos"]
                    and dup_player.js_number == player["js_number"]
                ):
                    return {
                        "message": f"Player {player['player_name']} already existed!"
                    }
            newPlayerDict = player
            for key, value in newPlayerDict.items():
                if value == "string":
                    return {"message": f"{key} is required."}
                if key == "player_bday" and not is_valid_age(value):
                    return {"message": "Player age is not legal"}

            count = db.query(func.max(Players.player_id)).scalar()
            newPlayerDict["player_id"] = (count or 0) + 1 + iter
            iter += 1
            newPlayerDict["player_club"] = new_db_club.club_id
            newPlayerDict["show"] = True
            new_db_player = Players(**newPlayerDict)

            db.add(new_db_player)

        db.commit()
        db.refresh(new_db_club)
        return {"message": "Created club and players successfully!"}
    except Exception as e:
        db.rollback()
        db.query(Clubs).filter(Clubs.club_name == new_club.club_name).delete()
        db.commit()

        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
