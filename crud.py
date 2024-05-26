from fastapi import HTTPException
from sqlalchemy import func
from core.db import db, db_deps
from schemas.db import Users, Clubs
from core.security import verify_password, get_password_hash
from api.deps import CurrentUser
from schemas.users import UserCreateBase
from schemas.clubs import Club_Create
from utils import is_valid_age, create_club_add_player


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
    newUserdict["user_id"] = 2 + (db.query(func.max(Users.user_id)).scalar() or 0)

    try:
        new_db_user = Users(**newUserdict)
        db.add(new_db_user)
        db.commit()

        return {"message": "Added user succesfully !"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Can't add new user: {str(e)}")


def create_club(db: db_deps, current_user: CurrentUser, new_club: Club_Create) -> Clubs | dict:
    new_club = new_club.dict()

    # check duplicated club_name:
    duplicated_name = db.query(Clubs).filter(Clubs.club_name == new_club['club_name']).first()
    if duplicated_name is not None:
        return {
            "message": f"{new_club['club_name']} has been used, please choose another club name !"
        }
    
    # check if current_user is another club's manager
    duplicated_manager = (
        db.query(Clubs).filter(Clubs.manager == current_user['user_id']).first()
    )
    if duplicated_manager is not None:
        return {
            "message": f"You can just create 1 club!"
        }


    # check not entered values
    for key, value in new_club.items():
        if value == "string":
            return {"message": f"{key} is required."}
    
    # auto complete data
    new_club["manager"] = current_user["user_id"]
    new_club["show"] = True

    # commit to database
    try:
        new_db_club = Clubs(**new_club)
        db.add(new_db_club)
        db.commit()
        create_club_add_player(db, new_db_club.club_id)
        return {"message": "Created club successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail = "Internal Server Error: Can't create new club")

    
