from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from core.config import config
from sqlalchemy import text
from typing import Annotated
from fastapi import Depends


class Database:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url, pool_size=100)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.Base = declarative_base()
        self.Base.metadata.create_all(bind=self.engine)

    def get_db(self):
        return self.SessionLocal()

    def get_base(self):
        return self.Base

    def query(self, model):
        return self.SessionLocal().query(model)

    def add(self, model):
        db = self.SessionLocal()
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    def commit(self):
        db = self.SessionLocal()
        db.commit()

    def refresh(self, model):
        db = self.SessionLocal()
        db.refresh(model)


print("Connecting to database...")
print(f"POSTGRES_SERVER: {config.POSTGRES_SERVER}")
print(f"POSTGRES_PORT: {config.POSTGRES_PORT}")
print(f"POSTGRES_DB: {config.POSTGRES_DB}")

db_url = f"postgresql://{config.POSTGRES_USER}:{config.POSTGRES_PASSWORD}@{config.POSTGRES_SERVER}:{config.POSTGRES_PORT}/{config.POSTGRES_DB}"
db = Database(db_url)
Base = db.get_base()
db_deps = Annotated[Session, Depends(db.get_db)]

print("Connected to database !")


def get_params(model, db: Session):
    try:
        params = db.query(model).first()
        return params
    # finally:
    #     db.close()
    except Exception as e:
        return {"message": f"Error: {str(e)}"}
