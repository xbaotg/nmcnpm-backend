from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated, Optional
from database import engine, SessionLocal
from sqlalchemy.orm import Session, load_only
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
import models


SECRET_KEYS = "sldfkvhjlLKHJOHoi234908uKHJOI098UJLKnkljlkdsjfLKHO8908U324HJL1JL"
ALGORITHM = "HS256"

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token')
TokenDep = Annotated[str, Depends(oauth2_bearer)]

def get_current_user(token: TokenDep):
    try:
        payload = jwt.decode(token, SECRET_KEYS, algorithms=[ALGORITHM])
        user_name: str = payload.get('sub')
        userid: int = payload.get('id')
        if user_name is None or userid is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

        return {'user_name': user_name, 'userid':userid}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

Current_user = Annotated[dict, Depends(get_current_user)]
user_dependency = Current_user

def get_user_permission(current_user: Current_user, db: db_dependency, role:str):
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
