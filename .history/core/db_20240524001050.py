from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import config
from sqlalchemy import text


class Database:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)
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
