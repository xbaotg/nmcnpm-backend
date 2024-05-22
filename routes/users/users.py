from datetime import date
from fastapi import FastAPI, HTTPException, Depends, APIRouter
from sqlalchemy import func

from routes.users.pydantics import *
import models
from auth import get_current_user, bcrypt_context
from main import db_dependency, user_dependency


route = APIRouter(
    prefix = '/users', 
    tags = ['users']
)


def get_user_permission(current_user: user_dependency, db: db_dependency, role:str):
    if current_user is None:
        raise HTTPException(status_code=401, detail = 'Authentication Failed')
        return None
    user_role = db.query(models.Users).filter(models.Users.userid == current_user['userid']).first().role


    #check permission of user_role
    if (role == "manager"):
        # check if user is deleted or not
        if (not db.query(models.Users).filter(models.Users.userid == current_user['userid']).first().show):
            raise HTTPException(status_code=401, detail="Your account is no longer active!")
        return True
    elif (role == "admin" and user_role != role):
        raise HTTPException(status_code=401, detail="You don't have permission to do this action!")

    return True
    

# CREATE new user  **admin only

def isValidAge(bday:date):
    now = date.today()
    age = now.year - bday.year - ((now.month, now.day) < (bday.month, bday.day))
    if (age < 16 or age > 40):
        return False
    return True

    
@route.post("/create-user")
async def create_user(newUser:UserCreateBase, db: db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")

    invalid_username = db.query(models.Users).filter(models.Users.user_name == newUser.user_name).first()
    if invalid_username:
        return {"message": "This username has already been taken, please choose another one!"}

    try:
        newUserdict = newUser.dict()
        for key, value in newUserdict.items():
            
            if (value == "string"):                    # kiem tra noi dung khong duoc nhap
                return {"message": f"{key} is required." }
            
            if (key == "user_bday"):                    # kiem tra tuoi 
                if not(isValidAge(value)):
                    return {"message": "User age is not legal"}

        # auto complete data
        if (newUserdict['role'] != "admin" and newUserdict['role'] != "manager"):
            return {"message": "Role must be 'admin' or 'manager'!"}
        newUserdict['password'] = bcrypt_context.hash(newUser.password)
        newUserdict['show'] = True
        count = db.query(func.max(models.Users.userid)).scalar()
        newUserdict['userid'] = count + 1

        new_db_user = models.Users(**newUserdict)

        db.add(new_db_user)
        db.commit()
        db.refresh(new_db_user)
        return new_db_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Can't add new user: {str(e)}")



#GET ALL USERS 

@route.get("/", response_model = List[User_res])
async def get_all_users(db:db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    
    db_user = db.query(models.Users).all()
    if db_user==0:
        raise HTTPException(status_code=404, detail='Cant find users')

    return db_user


# GET existing users (not deleted)  **admin only

@route.get("/get-activated-users", response_model = List[User_res])
async def get_all_users(db:db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    
    db_user = db.query(models.Users).filter(models.Users.show == True).all()
    if db_user==0:
        raise HTTPException(status_code=404, detail='Cant find users')

    return db_user


#GET deleted users

@route.get("/get-inactivated-users", response_model = List[User_res])
async def get_all_users(db:db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    
    db_user = db.query(models.Users).filter(models.Users.show == False).all()
    if db_user==0:
        raise HTTPException(status_code=404, detail='Cant find any users')

    return db_user


#GET user by name



# DELETE users (using put like update)

@route.put("/delete/{user_id}")
async def delete_user(user_id: int, db: db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db , "admin")             # check permission

    try:    
        db_user = db.query(models.Users).filter(models.Users.userid == user_id).first()
        if (db_user.show == True):
            db_user.show = False
            db.commit()
            return {"message": f"Deleted user with id:{user_id}"}
        else:
            return {"message": f"Can't find user with id:{user_id}. Maybe deleted."}
    except Exception as e:
        # db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)} !")


# Restore deleted users
@route.put("/restore-deleted-user/{user_id}")
async def delete_user(user_id: int, db: db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    try:    
        db_user = db.query(models.Users).filter(models.Users.userid == user_id).first()
        if (db_user.show != True):
            db_user.show = True
            db.commit()
            return {"message": f"Restored user with id:{user_id}"}
        else:
            return {"message": f"Can't find user with id:{user_id}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)} !")



#Update users

@route.put("/update-user-info/{user_id}", response_model=UserUpdate)
async def update_user_info(db: db_dependency, user_id: int, newinfo:UserUpdate, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    try: 
        target = db.query(models.Users).filter(models.Users.userid == user_id).first()
        
        update_info = newinfo.dict(exclude_unset=True)
        print(update_info)

        for key, value in update_info.items(): #  
            if (value == "string"):
                continue
            if (value == date.today()):
                continue
            setattr(target, key, value)
        db.commit()
        db.refresh(target)

        return target
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}!")
    