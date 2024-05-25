from datetime import timedelta
from typing import Annotated

from core.db import db_deps
from core.security import create_access_token
from crud import authenticate_user
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth import Token
from starlette import status


router = APIRouter()


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_deps
):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INCORRECT USERNAME OR PASSWORD.",
            )

        token = create_access_token(user.user_name, user.user_id, timedelta(minutes=20))
        return {"access_token": token, "token_type": "bearer"}
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"My bad: {str(e)}")
