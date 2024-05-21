from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Date
from database import Base

class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True, index=True)
    
    question_text = Column(String, index=True)

class Choices(Base):
    __tablename__ = 'choices'

    id = Column(Integer, primary_key=True, index=True)

    choice_text = Column(String, index=True)
    is_correct = Column(Boolean, default=False)
    question_id = Column(Integer, ForeignKey("questions.id"))

class Users(Base):
    __tablename__ = 'users'

    userid = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fullname = Column(String, index=True)
    role = Column(String, index=True)
    user_name = Column(String, index=True)
    password = Column(String, index=True)
    user_nation = Column(String, index=True)
    user_bday = Column(Date, index=True)
    user_mail = Column(String, index=True)
    show = Column(Boolean, index=True)

class Clubs(Base):
    __tablename__ = 'clubs'

    clubid = Column(Integer, primary_key=True, index=True)
    club_name = Column(String, index=True)
    total_player = Column(Integer, index=True)
    nation  = Column(String, index=True)
    manager = Column(Integer, ForeignKey("Users.userid"), index=True)
    club_shortname = Column(String, index=True)
    show = Column(Boolean, index=True)

class Players(Base):
    __tablename__ = 'players'

    player_id = Column(Integer, primary_key=True, index=True)
    player_name = Column(String, index=True)
    player_bday = Column(Date, index=True)
    player_club = Column(Integer, ForeignKey("Clubs.clubid"), index =True)
    player_pos = Column(String, index=True)
    js_number = Column(Integer, index=True)
    show = Column(Boolean, index=True)