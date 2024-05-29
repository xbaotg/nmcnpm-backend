from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date, Time
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

    club_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    club_name = Column(String, index=True)
    club_shortname = Column(String, index=True)
    total_player = Column(Integer, index=True)
    manager = Column(Integer, ForeignKey("users.user_id"), index=True)
    show = Column(Boolean, index=True)


class Players(Base):
    __tablename__ = "players"

    player_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    player_name = Column(String, index=True)
    player_bday = Column(Date, index=True)
    player_club = Column(Integer, ForeignKey("clubs.club_id"), index=True)
    player_pos = Column(String, index=True)
    player_nation = Column(String, index=True)
    js_number = Column(Integer, index=True)
    show = Column(Boolean, index=True)




class Params(Base):
    __tablename__ = "params"

    id = Column(Integer, primary_key=True, autoincrement=True)
    min_player_age = Column(Integer, index = True)
    max_player_age = Column(Integer, index=True)
    min_club_player = Column(Integer, index=True)
    max_club_player = Column(Integer, index=True)
    max_foreign_player = Column(Integer, index=True)
    
    points_win = Column(Integer, index=True)
    points_draw = Column(Integer, index=True)
    points_lose = Column(Integer, index=True)

    max_goal_types = Column(Integer, index=True)
    max_goal_time = Column(Time, index=True)

class Referees(Base):
    __tablename__ = "referees"

    ref_id = Column(Integer, primary_key=True, index=True)
    ref_name = Column(String, index=True)
    ref_birthd = Column(String, index=True)
    ref_nation = Column(String, index=True)
    ref_mail = Column(String, index=True)
    show = Column(Boolean, index=True)


