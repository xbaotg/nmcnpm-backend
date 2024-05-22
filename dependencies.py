from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Annotated, Optional
from database import engine, SessionLocal
from sqlalchemy.orm import Session, load_only
from auth import get_current_user, bcrypt_context

def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally: 
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]