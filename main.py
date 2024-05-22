from datetime import date
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated, Optional

import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session, load_only
from sqlalchemy import func

#import routes
from auth import bcrypt_context, router as auth_route
from routes.users.users import route as user_route



models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(auth_route)
app.include_router(user_route)


