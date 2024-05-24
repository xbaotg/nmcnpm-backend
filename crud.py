from fastapi import HTTPException
from sqlalchemy import func
from core.db import db, db_deps
from schemas.db import Users
from core.security import verify_password, get_password_hash
from schemas.users import UserCreateBase
from utils import is_valid_age



def authenticate_user(username: str, password: str):
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
    try:
        newUserdict = new_user.dict()

        for key, value in newUserdict.items():
            if value == "string":  # kiem tra noi dung khong duoc nhap
                return {"message": f"{key} is required."}

            if key == "user_bday":  # kiem tra tuoi
                if not is_valid_age(value):
                    return {"message": "User age is not legal"}

        # auto complete data
        if newUserdict["role"] != "admin" and newUserdict["role"] != "manager":
            return {"message": "Role must be 'admin' or 'manager'!"}

        newUserdict["password"] = get_password_hash(newUserdict["password"])
        newUserdict["show"] = True
        newUserdict["user_id"] = 1 + (db.query(func.max(Users.user_id)).scalar() or 0)

        new_db_user = Users(**newUserdict)
        db.add(new_db_user)
        db.commit()

        return new_db_user

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Can't add new user: {str(e)}")
