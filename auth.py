from datetime import timedelta, datetime, date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from passlib.context import CryptContext
from sqlalchemy import func
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

from dependencies import models, db_dependency 

SECRET_KEYS = "sldfkvhjlLKHJOHoi234908uKHJOI098UJLKnkljlkdsjfLKHO8908U324HJL1JL"
ALGORITHM = "HS256"
router = APIRouter(
    prefix = '/auth',
    tags = ['auth']
)


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token')


class Token(BaseModel):
    access_token : str
    token_type : str


@router.post("/token", response_model = Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="INCORRECT USERNAME OR PASSWORD.")
    
    token = create_access_token(user.user_name, user.userid, timedelta(minutes = 20))
    return {'access_token': token, 'token_type': 'bearer'}

def authenticate_user(username: str, password: str, db: db_dependency):
    try:
        user = db.query(models.Users).filter(models.Users.user_name == username).first()
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"The error is : {str(e)}")
    if not user:
        return False

    try:
        if not bcrypt_context.verify(password, user.password):
            return False
    except Exception:
        if user.password != password:
            return False

    return user

def create_access_token(username: str, userid: int, expired_delta: timedelta):
    encode = {'sub': username, 'id': userid}
    expires = datetime.utcnow() + expired_delta
    encode.update({'exp': expires})
    try:
        return jwt.encode(encode, SECRET_KEYS, algorithm=ALGORITHM)
    except Exception as e:
        raise HTTPException(status_code=501, detail=f"The error is in encoding jwt : {str(e)}")



def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEYS, algorithms=[ALGORITHM])
        user_name: str = payload.get('sub')
        userid: int = payload.get('id')
        if user_name is None or userid is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

        return {'user_name': user_name, 'userid':userid}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')

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