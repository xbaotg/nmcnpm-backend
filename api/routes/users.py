from datetime import date, datetime

from core.db import db_deps, db, get_params
from crud import create_user, get_info_user
from fastapi import APIRouter, HTTPException, Depends
from schemas.db import Users, Params
from schemas.users import UserCreateBase, UserReg, UserUpdate
from sqlalchemy import func

from api.deps import List, CurrentUser, get_password_hash, fuzz
from utils import unix_to_date, date_to_unix

route = APIRouter()


def create_user_res(user):
    res = {
        "user_id": user.user_id,
        "full_name": user.full_name,
        "role": user.role,
        "user_name": user.user_name,
        "user_mail": user.user_mail,
        "user_nation": user.user_nation,
        "user_bday": user.user_bday,
        "show": user.show,
    }
    return res


def get_user_permission(db: db_deps, current_user: CurrentUser, role: str):
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail={"status": "error", "message": "Authentication Failed"},
        )

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role
    )

    if role == "manager":
        if (
            not db.query(Users)
            .filter(Users.user_id == current_user["user_id"])
            .first()
            .show
        ):
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "error",
                    "message": "Your account is no longer active!",
                },
            )

        return True
    elif role == "admin" and user_role != role:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "You don't have permission to do this action!",
            },
        )

    return True


@route.post("/create-user")
async def create_user_route(
    db: db_deps, current_user: CurrentUser, new_user: UserCreateBase
):
    hasPermission = get_user_permission(db, current_user, "admin")

    try:
        user = create_user(db, new_user)
        return {
            "status": "success",
            "message": "User created successfully!",
            "data": user,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@route.get("/")
async def get_all_users(current_user: CurrentUser, db: db_deps):
    try:
        hasPermission = get_user_permission(db, current_user, "admin")
        db_users = db.query(Users).all()

        res = [create_user_res(user) for user in db_users]
        return {"status": "success", "data": res}
    except Exception as e:
        return {"status": "error", "message": f"Internal server error: {str(e)}"}


@route.get("/me")
async def get_user_info(current_user: CurrentUser, db: db_deps):
    try:
        res = get_info_user(db, current_user)
        return {"status": "success", "data": res}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# GET existing users (not deleted)
@route.get("/get-activated-users")
async def get_activated_users(current_user: CurrentUser, db: db_deps):
    hasPermission = get_user_permission(db, current_user, "admin")

    db_users = db.query(Users).filter(Users.show == True).all()
    if db_users == None:
        return {"status": "error", "message": "Can't find users"}
    res = [create_user_res(user) for user in db_users]
    return {"status": "success", "data": res}


# GET deleted users
@route.get("/get-inactivated-users")
async def get_inactivated_users(current_user: CurrentUser, db: db_deps):
    hasPermission = get_user_permission(db, current_user, "admin")

    db_users = db.query(Users).filter(Users.show == False).all()
    if db_users == None:
        return {"status": "error", "message": "Can't find users"}
    res = [create_user_res(user) for user in db_users]
    return {"status": "success", "data": res}


# DELETE users (using put like update)
@route.put("/delete/{target_user_id}")
async def delete_user(target_user_id: int, current_user: CurrentUser, db: db_deps):
    hasPermission = get_user_permission(db, current_user, "admin")
    try:
        db_user = db.query(Users).filter(Users.user_id == target_user_id).first()

        if db_user is None:
            return {
                "status": "error",
                "message": f"Can't find user with id: {target_user_id}",
            }

        if db_user.show == True:
            db_user.show = False
            db.commit()
            return {
                "status": "success",
                "message": f"Deleted user with id: {target_user_id}",
            }
        else:
            return {
                "status": "error",
                "message": f"Can't find user with id: {target_user_id}. Maybe deleted.",
            }

    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


# Restore deleted users
@route.put("/restore-deleted-user/{user_id}")
async def restore_deleted_user(user_id: int, current_user: CurrentUser, db: db_deps):
    hasPermission = get_user_permission(db, current_user, "admin")
    try:
        db_user = db.query(Users).filter(Users.user_id == user_id).first()
        if db_user.show != True:
            db_user.show = True
            db.commit()
            return {"status": "success", "message": f"Restored user with id: {user_id}"}
        else:
            return {"status": "error", "message": f"Can't find user with id: {user_id}"}
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


# Permanently delete user
@route.delete("/permanently-delete/{user_id}")
async def permanently_delete_user(user_id: int, db: db_deps, current_user: CurrentUser):
    hasPermission = get_user_permission(db, current_user, "admin")

    target = db.query(Users).filter(Users.user_id == user_id).first()

    db.delete(target)
    db.commit()
    return {
        "status": "success",
        "message": f"Delete user with id {user_id} successfully !",
    }


# Update users
@route.put("/update-user-info/{user_id}")
async def update_user_info(
    user_id: int, new_info: UserUpdate, current_user: CurrentUser, db: db_deps
):
    hasPermission = get_user_permission(db, current_user, "admin")
    try:
        target = db.query(Users).filter(Users.user_id == user_id).first()

        update_info = new_info.dict(exclude_unset=True)

        for key, value in update_info.items():
            if value == "string":
                continue
            if key == "user_bday":
                if value == 0:
                    continue
            if key == "password":
                value = get_password_hash(value)
            setattr(target, key, value)

        db.commit()
        db.refresh(target)

        return {
            "status": "success",
            "data": {
                "full_name": target.full_name,
                "role": target.role,
                "user_name": target.user_name,
                "password": new_info.password,
                "user_nation": target.user_nation,
                "user_bday": target.user_bday,
                "user_mail": target.user_mail,
            },
        }
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


# SEARCH
# search by name
@route.get("/search-by-name")
async def search_user_by_name(
    full_name: str, db: db_deps, current_user: CurrentUser, threshold: int = 80
):
    try:
        activated_users = db.query(Users).filter(Users.show == True).all()
        matched_users = (
            user
            for user in activated_users
            if fuzz.partial_ratio(user.full_name.lower(), full_name.lower())
            >= threshold
        )
        if not matched_users:
            return {
                "status": "error",
                "message": f"Can't find any users match the name: {full_name}",
            }

        res = [create_user_res(user) for user in matched_users]
        return {"status": "success", "data": res}
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}


# search by nation
@route.get("/search-by-nation")
async def search_user_by_nation(
    nation: str, db: db_deps, current_user: CurrentUser, threshold: int = 80
):
    try:
        activated_users = db.query(Users).filter(Users.show == True).all()
        matched_users = (
            user
            for user in activated_users
            if fuzz.partial_ratio(user.user_nation.lower(), nation.lower()) >= threshold
        )
        if not matched_users:
            return {
                "status": "error",
                "message": f"Can't find any users match the nation: {nation}",
            }
        res = [create_user_res(user) for user in matched_users]
        return {"status": "success", "data": res}
    except Exception as e:
        return {"status": "error", "message": f"Internal Server Error: {str(e)}"}
