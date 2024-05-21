from datetime import date
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated, Optional

import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session, load_only
from sqlalchemy import func
from Users import test
from auth import get_current_user, bcrypt_context
import auth
# from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date

app = FastAPI()
app.include_router(auth.router)
models.Base.metadata.create_all(bind=engine)

class ChoiceBase(BaseModel):
    choice_text: str
    is_correct: bool

class QuestionBase(BaseModel):
    question_text: str
    choices: list[ChoiceBase]

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


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
    

@app.get("/questions/{question_id}")
async def read_question(question_id: int, db: db_dependency, current_user:user_dependency):
    user_role = get_user_permission(current_user, db, "manager")
    result = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not result:
        raise HTTPException(status_code=404, detail='Question not found')
    return result

@app.post("/questions/")
async def create_question(question:QuestionBase, db: db_dependency):
    db_question = models.Question(question_text=question.question_text)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)

    for choice in question.choices:
        db_choice=models.Choices(choice_text=choice.choice_text, is_correct=choice.is_correct, question_id = db_question.id)

        db.add(db_choice)
    
    db.commit()


# CREATE new user  **admin only

def isValidAge(bday:date):
    now = date.today()
    age = now.year - bday.year - ((now.month, now.day) < (bday.month, bday.day))
    if (age < 16 or age > 40):
        return False
    return True

class UserCreateBase(BaseModel):
    fullname: str
    role: str  
    user_name : str 
    password: str 
    user_nation: str 
    user_bday: date
    user_mail: str 
    
@app.post("/users/create-user")
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


# GET
class User_res(BaseModel):
    userid: int
    fullname: str
    role : str
    user_name : str
    user_mail : str
    user_bday: date
    show: bool
    class Config: 
        orm_mode = True

#GET ALL USERS 
@app.get("/users/", response_model = List[User_res])
async def get_all_users(db:db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    
    db_user = db.query(models.Users).all()
    if db_user==0:
        raise HTTPException(status_code=404, detail='Cant find users')

    return db_user

# GET existing users (not deleted)  **admin only
@app.get("/users/get-users", response_model = List[User_res])
async def get_all_users(db:db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    
    db_user = db.query(models.Users).filter(models.Users.show == True).all()
    if db_user==0:
        raise HTTPException(status_code=404, detail='Cant find users')

    return db_user


#GET deleted users
@app.get("/users/get-deleted-users", response_model = List[User_res])
async def get_all_users(db:db_dependency, current_user: user_dependency):
    hasPermission = get_user_permission(current_user, db, "admin")
    
    db_user = db.query(models.Users).filter(models.Users.show == False).all()
    if db_user==0:
        raise HTTPException(status_code=404, detail='Cant find any users')

    return db_user
#GET user by name


# DELETE users (using put like update)
@app.put("/users/delete/{user_id}")
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
@app.put("/users/restore-deleted-user/{user_id}")
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
        # db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)} !")



#Update users
class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    role: Optional[str] = None
    user_name: Optional[str] = None
    password: Optional[str] = None
    user_nation: Optional[str] = None
    user_bday: Optional[date] = None
    user_mail: Optional[str] = None
    user_nation: Optional[str] = None

@app.put("/user/update-user-info/{user_id}", response_model=UserUpdate)
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
    
    
