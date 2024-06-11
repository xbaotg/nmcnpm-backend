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


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_deps
):
    try:
        response = authenticate_user(form_data.username, form_data.password, db)

        if response.get("status") == "error":
            return {"status": "error", "message": "Incorrect username or password."}

        user = response.get("data")

        token = create_access_token(
            user.user_name, user.user_id, timedelta(minutes=1440)
        )

        print(token, config.SECRET_KEY, config.ALGORITHM)

        # get expired date
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        expired_date = payload.get("exp")

        return {
            # "status": "success",
            # "message": "Token created successfully.",
            # "data": {
            "access_token": token,
            "token_type": "bearer",
            "expired_date": expired_date,
            # },
        }

    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}

    except Exception as e:
        print(f"My bad: {str(e)}")
        return {"status": "error", "message": "Internal Server Error."}
