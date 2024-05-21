from datetime import timedelta, datetime, date
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import func
import models


router = APIRouter(
    prefix = '/auth',
    tags = ['auth']
)

SECRET_KEYS = "sldfkvhjlLKHJOHoi234908uKHJOI098UJLKnkljlkdsjfLKHO8908U324HJL1JL"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token')

class CreateUserRequest(BaseModel):
    user_name: str
    password: str
    fullname: str
    user_nation: str
    user_bday: date
    user_mail: str


class Token(BaseModel):
    access_token : str
    token_type : str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# @router.post("/", status_code=status.HTTP_201_CREATED)  # create a new user-default role = manager
# async def create_user(db: db_dependency, create_user_req: CreateUserRequest):
#     maxID = db.query(func.max(models.Users.userid)).scalar()
    
#     invalid_username = db.query(models.Users).filter(models.Users.user_name == create_user_req.user_name).first()
#     if invalid_username:
#         return {"message": "This username has already been taken, please choose another one!"}

#     create_user_model = Users(
#         userid = maxID + 1,
#         role = "manager",
#         user_name = create_user_req.user_name,
#         password = bcrypt_context.hash(create_user_req.password),
#         fullname = create_user_req.fullname,
#         user_nation = create_user_req.user_nation,
#         user_bday = create_user_req.user_bday,
#         user_mail = create_user_req.user_mail
#     )

#     db.add(create_user_model)
#     db.commit()
#     return create_user_req





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