from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_, text

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Events, Matches, Ranking
from schemas.ranking import InitRank, Criteria
from utils import (
    get_params,
)

route = APIRouter()


# RANKING BY SCORE
"""
idea sẽ là lặp qua tất cả các clubs, tạo 1 object với khóa là club id

lặp qua all events, với mỗi event update các thông số cho 2 object tương ứng với 
"""


# INIT CLUBS TO RANK TABLE
@route.get("/init-rank")
async def init_rank(db: db_deps):
    clubs = (
        db.query(Clubs).filter(Clubs.show == True).order_by(Clubs.club_id.desc()).all()
    )
    for club in clubs:
        target = Ranking(
            club_id=club.club_id,
            club_ranking=None,
            club_points=None,
            club_win=None,
            club_draw=None,
            club_lost=None,
            club_goals=None,
            club_gconcede=None,
            club_gdif=None,
            show=True,
        )

        db.add(target)

    db.commit()
    ranks = db.query(Ranking).filter(Ranking.show == True).all()
    return ranks


# update values for ranking with every matches
# --> too long (query all matches ~ 300 matches)
# --> create update values function, call after update a match
@route.put("/update-values")
async def update_ranking_values(db: db_deps):
    # take values from finished matches
    matches = (
        db.query(Matches).filter(Matches.show == True, Matches.finish != None).all()
    )

    # get params to calculate points
    params = get_params(Params, db)

    # for each match, update values for clubs
    for match in matches:
        rank_club1 = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_id == match.team1)
            .first()
        )
        rank_club2 = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_id == match.team2)
            .first()
        )

        # update goals
        rank_club1.club_goals = (rank_club1.club_goals or 0) + match.goal1
        rank_club2.club_goals = (rank_club2.club_goals or 0) + match.goal2

        # update away_goals (team2 is away team)
        rank_club2.away_goals = (rank_club2.away_goals or 0) + match.goal2

        # update win/lose/draw
        if match.goal1 == match.goal2:  # draw
            rank_club1.club_draw = (rank_club1.club_draw or 0) + 1
            rank_club2.club_draw = (rank_club2.club_draw or 0) + 1

        elif match.goal1 < match.goal2:  # team1 lost - team2 win
            rank_club1.club_lost = (rank_club1.club_lost or 0) + 1
            rank_club2.club_win = (rank_club2.club_win or 0) + 1

        else:  # team1 win - team2 lost
            rank_club1.club_win = (rank_club1.club_win or 0) + 1
            rank_club2.club_lost = (rank_club2.club_lost or 0) + 1

        db.commit()

        # update  club_points
        rank_club1.club_points = (
            (rank_club1.club_win or 0) * params.points_win
            + (rank_club1.club_draw or 0) * params.points_draw
            + (rank_club1.club_lost or 0) * params.points_lose
        )
        rank_club2.club_points = (
            (rank_club2.club_win or 0) * params.points_win
            + (rank_club2.club_draw or 0) * params.points_draw
            + (rank_club2.club_lost or 0) * params.points_lose
        )

        # update club_gdif (goals made - goals made by opponents)
        rank_club1.club_gdif = (rank_club1.club_gdif or 0) + match.goal1 - match.goal2
        rank_club2.club_gdif = (rank_club2.club_gdif or 0) + match.goal2 - match.goal1


@route.get("/ranking")
async def ranking(db: db_deps, crit: Criteria, desc: bool = True):
    if crit == "points":
        rankings = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_points == None)
            .all()
        )
        for ranking in rankings:
            ranking.club_points = 0

        db.commit()
        if desc:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_points.desc())
                .all()
            )
        else:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_points.asc())
                .all()
            )

        return rankings
    if crit == "goals":
        rankings = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_goals == None)
            .all()
        )
        for ranking in rankings:
            ranking.club_goals = 0

        db.commit()
        if desc:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_goals.desc())
                .all()
            )
        else:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_goals.asc())
                .all()
            )

        return rankings
    if crit == "away_goals":
        rankings = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.away_goals == None)
            .all()
        )
        for ranking in rankings:
            ranking.away_goals = 0

        db.commit()
        if desc:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.away_goals.desc())
                .all()
            )
        else:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.away_goals.asc())
                .all()
            )

        return rankings
    if crit == "gdif":
        rankings = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_gdif == None)
            .all()
        )
        for ranking in rankings:
            ranking.club_gdif = 0

        db.commit()
        if desc:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_gdif.desc())
                .all()
            )
        else:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_gdif.asc())
                .all()
            )

        return rankings
    if crit == "win":
        rankings = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_win == None)
            .all()
        )
        for ranking in rankings:
            ranking.club_win = 0

        db.commit()
        if desc:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_win.desc())
                .all()
            )
        else:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_win.asc())
                .all()
            )

        return rankings
    if crit == "draw":
        rankings = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_draw == None)
            .all()
        )
        for ranking in rankings:
            ranking.club_draw = 0

        db.commit()
        if desc:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_draw.desc())
                .all()
            )
        else:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_draw.asc())
                .all()
            )

        return rankings

    if crit == "lost":
        rankings = (
            db.query(Ranking)
            .filter(Ranking.show == True, Ranking.club_lost == None)
            .all()
        )
        for ranking in rankings:
            ranking.club_lost = 0

        db.commit()
        if desc:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_lost.desc())
                .all()
            )
        else:
            rankings = (
                db.query(Ranking)
                .filter(Ranking.show == True)
                .order_by(Ranking.club_lost.asc())
                .all()
            )

        return rankings
