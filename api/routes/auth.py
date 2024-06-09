from datetime import timedelta, datetime
from typing import Annotated

from core.db import db_deps
from core.security import create_access_token
from core.config import config
from jose import jwt

from crud import authenticate_user
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from schemas.auth import Token
from starlette import status


router = APIRouter()


@router.post("/token", response_model=Token | dict)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_deps
):
    try:
        user = authenticate_user(form_data.username, form_data.password, db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="INCORRECT USERNAME OR PASSWORD.",
            )

        token = create_access_token(
            user.user_name, user.user_id, timedelta(minutes=1440)
        )

        # get expired date
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        expired_date = payload.get("exp")

        return {
            "access_token": token,
            "token_type": "bearer",
            "expired_date": expired_date,
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        print(f"My bad: {str(e)}")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="INTERNAL SERVER ERROR.",
        )
