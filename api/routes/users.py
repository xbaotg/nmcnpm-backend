from datetime import date

from core.db import db
from crud import create_user
from fastapi import APIRouter, HTTPException
from schemas.db import Users
from schemas.users import UserCreateBase, UserReg
from sqlalchemy import func

route = APIRouter()


def get_user_permission(current_user, role):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    # check permission of user_role
    if role == "manager":
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
    elif role == "admin" and user_role != role:
        raise HTTPException(
            status_code=401, detail="You don't have permission to do this action!"
        )

    return True


@route.post("/create-user")
async def create_user(new_user: UserCreateBase):
    invalid_username = (
        db.query(Users).filter(Users.user_name == new_user.user_name).first()
    )

    if invalid_username:
        return {
            "message": "This username has already been taken, please choose another one!"
        }

    await create_user(new_user)


# GET ALL USERS


@route.get("/", response_model=list[UserReg])
async def get_all_users(current_user):
    db_user = db.query(Users).all()

    if db_user == 0:
        raise HTTPException(status_code=404, detail="Cant find users")

    return db_user


# GET existing users (not deleted)  **admin only
# @route.get("/get-activated-users", response_model=List[UserReg])
# async def get_all_users(current_user: user_dependency):
#     hasPermission = get_user_permission(current_user, db, "admin")

#     db_user = db.query(db.Users).filter(db.Users.show == True).all()
#     if db_user == 0:
#         raise HTTPException(status_code=404, detail="Cant find users")

#     return db_user


# GET deleted users


# @route.get("/get-inactivated-users", response_model=List[UserReg])
# async def get_all_users(db: db_dependency, current_user: user_dependency):
#     hasPermission = get_user_permission(current_user, db, "admin")

#     db_user = db.query(db.Users).filter(db.Users.show == False).all()
#     if db_user == 0:
#         raise HTTPException(status_code=404, detail="Cant find any users")

#     return db_user


# GET user by name


# DELETE users (using put like update)


# @route.put("/delete/{user_id}")
# async def delete_user(user_id: int, current_user: user_dependency):
#     try:
#         db_user = db.query(Users).filter(Users.userid == user_id).first()

#         if db_user is None:
#             raise HTTPException(
#                 status_code=404, detail="Can't find user with id:{user_id}"
#             )

#         if db_user.show == True:
#             db_user.show = False
#             db.commit()
#             return {"message": f"Deleted user with id:{user_id}"}
#         else:
#             return {"message": f"Can't find user with id:{user_id}. Maybe deleted."}

#     except Exception as e:
#         # db.rollback()
#         raise HTTPException(
#             status_code=500, detail=f"Internal Server Error: {str(e)} !"
#         )


# # Restore deleted users
# @route.put("/restore-deleted-user/{user_id}")
# async def delete_user(user_id: int, current_user: user_dependency):
#     try:
#         db_user = db.query(db.Users).filter(db.Users.userid == user_id).first()
#         if db_user.show != True:
#             db_user.show = True
#             db.commit()
#             return {"message": f"Restored user with id:{user_id}"}
#         else:
#             return {"message": f"Can't find user with id:{user_id}."}
#     except Exception as e:
#         raise HTTPException(
#             status_code=500, detail=f"Internal Server Error: {str(e)} !"
#         )


# # Update users


# @route.put("/update-user-info/{user_id}", response_model=UserUpdate)
# async def update_user_info(
#     user_id: int, new_info: UserUpdate, current_user: user_dependency
# ):
#     hasPermission = get_user_permission(current_user, db, "admin")
#     try:
#         target = db.query(Users).filter(Users.userid == user_id).first()

#         update_info = new_info.dict(exclude_unset=True)
#         print(update_info)

#         for key, value in update_info.items():  #
#             if value == "string":
#                 continue
#             if value == date.today():
#                 continue
#             setattr(target, key, value)

#         db.commit()
#         db.refresh(target)

#         return target
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}!")
