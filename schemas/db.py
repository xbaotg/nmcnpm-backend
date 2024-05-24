from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from core.db import Base


class Users(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    full_name = Column(String, index=True)
    role = Column(String, index=True)
    user_name = Column(String, index=True)
    password = Column(String, index=True)
    user_nation = Column(String, index=True)
    user_bday = Column(Date, index=True)
    user_mail = Column(String, index=True)
    show = Column(Boolean, index=True)


class Clubs(Base):
    __tablename__ = "clubs"

    clubid = Column(Integer, primary_key=True, index=True)
    club_name = Column(String, index=True)
    total_player = Column(Integer, index=True)
    nation = Column(String, index=True)
    manager = Column(Integer, ForeignKey("users.userid"), index=True)
    club_shortname = Column(String, index=True)
    show = Column(Boolean, index=True)


class Players(Base):
    __tablename__ = "players"

    player_id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    player_bday = Column(Date, index=True)
    player_club = Column(Integer, ForeignKey("clubs.clubid"), index=True)
    player_pos = Column(String, index=True)
    player_nation = Column(String, index=True)
    js_number = Column(Integer, index=True)
    show = Column(Boolean, index=True)
