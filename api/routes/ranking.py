from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_, text

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Events, Matches, Ranking
from schemas.ranking import InitRank, Criteria, RankingRes
from utils import get_params, datetime_to_unix

route = APIRouter()


# RANKING BY SCORE
"""
idea sẽ là lặp qua tất cả các clubs, tạo 1 object với khóa là club id

lặp qua all events, với mỗi event update các thông số cho 2 object tương ứng với 
"""


def create_RankingRes(db: db_deps, r: Ranking):

    # find next match
    next_match = (
        db.query(Matches)
        .filter(
            Matches.show == True,
            or_(Matches.team1 == r.club_id, Matches.team2 == r.club_id),
            Matches.start > datetime_to_unix(datetime.now()),
        )
        .order_by(Matches.start.asc())
        .first()
    )

    if next_match:
        next_match_id = next_match.match_id
    else:
        next_match_id = None

    # find recent matches
    recent_matches = []
    recents = (
        db.query(Matches)
        .filter(
            Matches.show == True,
            or_(Matches.team1 == r.club_id, Matches.team2 == r.club_id),
            Matches.start < datetime_to_unix(datetime.now()),
        )
        .order_by(Matches.start.desc())
        .all()
    )

    for recent in recents:
        if len(recent_matches) > 5:
            break
        recent_matches.append(recent.match_id)

    # create return
    res = RankingRes(
        club_id=r.club_id,
        away_goals=r.away_goals,
        club_points=r.club_points,
        club_win=r.club_win,
        club_draw=r.club_draw,
        club_lost=r.club_lost,
        club_goals=r.club_goals,
        club_gconcede=0,
        club_gdif=r.club_gdif,
        recent_matches=recent_matches,
        next_match=next_match_id,
        show=r.show,
    )
    return res


@route.get("/ranking")
async def ranking(db: db_deps, crit: Criteria, desc: bool = True):
    if crit == "points":
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

        res = []
        for ranking in rankings:
            res.append(create_RankingRes(db, ranking))

        return res
    if crit == "goals":
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


# INIT CLUBS TO RANK TABLE
@route.get("/init-rank")
async def init_rank(db: db_deps):
    clubs = (
        db.query(Clubs).filter(Clubs.show == True).order_by(Clubs.club_id.desc()).all()
    )
    for club in clubs:
        target = Ranking(
            club_id=club.club_id,
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

    # reset all values before updating
    rankings = db.query(Ranking).filter(Ranking.show == True).all()
    for ranking in rankings:
        ranking.away_goals = 0
        ranking.club_points = 0
        ranking.club_goals = 0
        ranking.club_gdif = 0
        ranking.club_win = 0
        ranking.club_draw = 0
        ranking.club_lost = 0
        ranking.club_gconcede = 0

    db.commit()

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

        # update gconcede
        rank_club1.club_gconcede += match.goal2
        rank_club2.club_gconcede += match.goal1

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


@route.get("/rank-with-priority")
async def rank_with_priority(
    db: db_deps,
    crit1: Criteria,
    crit2: Criteria = Criteria.none,
    crit3: Criteria = Criteria.none,
    crit4: Criteria = Criteria.none,
    crit5: Criteria = Criteria.none,
    desc: bool = True,
):
    # create attributes names
    crit1 = str(crit1).replace("Criteria.", "")
    crit2 = str(crit2).replace("Criteria.", "")
    crit3 = str(crit3).replace("Criteria.", "")
    crit4 = str(crit4).replace("Criteria.", "")
    crit5 = str(crit5).replace("Criteria.", "")

    if crit2 == "none":
        crit2 = crit1
    if crit3 == "none":
        crit3 = crit1
    if crit4 == "none":
        crit4 = crit1
    if crit5 == "none":
        crit5 = crit1

    # query and order
    query = db.query(Ranking).filter(Ranking.show == True)

    if desc:
        query = query.order_by(
            getattr(Ranking, crit1).desc(),
            getattr(Ranking, crit2).desc(),
            getattr(Ranking, crit3).desc(),
            getattr(Ranking, crit4).desc(),
            getattr(Ranking, crit5).desc(),
        )
    else:
        query = query.order_by(
            getattr(Ranking, crit1),
            getattr(Ranking, crit2),
            getattr(Ranking, crit3),
            getattr(Ranking, crit4),
            getattr(Ranking, crit5),
        )

    results = query.all()

    return results


# class Ranking(Base):
#     __tablename__ = "ranking"

#     club_id = Column(Integer, ForeignKey("clubs.club_id"), primary_key=True, index=True)
#     away_goals = Column(Integer, index=True)
#     club_points = Column(Integer, index=True)
#     club_win = Column(Integer, index=True)
#     club_draw = Column(Integer, index=True)
#     club_lost = Column(Integer, index=True)
#     club_goals = Column(Integer, index=True)
#     club_gconcede = Column(Integer, index=True)
#     club_gdif = Column(Integer, index=True)
#     show = Column(Boolean, index=True)


@route.get("/get")
async def rank_baotg(db: db_deps):
    priority = db.query(Params).first().priority.split(";")

    matches = db.query(Matches).filter(Matches.show == True).all()
    clubs = db.query(Clubs).filter(Clubs.show == True).all()
    results = {}

    for club in clubs:
        results[club.club_id] = {
            "club_id": club.club_id,
            "away_goals": 0,
            "club_points": 0,
            "club_win": 0,
            "club_draw": 0,
            "club_lost": 0,
            "club_goals": 0,
            "club_gconcede": 0,
            "club_gdif": 0,
            "show": True,
        }

    for match in matches:
        results[match.team1]["club_goals"] += match.goal1
        results[match.team2]["club_goals"] += match.goal2
        results[match.team2]["away_goals"] += match.goal2
        results[match.team1]["club_gconcede"] += match.goal2
        results[match.team2]["club_gconcede"] += match.goal1

        if match.goal1 == match.goal2:
            results[match.team1]["club_draw"] += 1
            results[match.team2]["club_draw"] += 1
        elif match.goal1 < match.goal2:
            results[match.team1]["club_lost"] += 1
            results[match.team2]["club_win"] += 1
        else:
            results[match.team1]["club_win"] += 1
            results[match.team2]["club_lost"] += 1

    for club in clubs:
        results[club.club_id]["club_points"] = (
            results[club.club_id]["club_win"] * 3 + results[club.club_id]["club_draw"]
        )
        results[club.club_id]["club_gdif"] = (
            results[club.club_id]["club_goals"] - results[club.club_id]["club_gconcede"]
        )

    index = priority.index("h")

    mapping_priority = {
        "p": "club_points",
        "d": "club_gdif",
        "g": "club_goals",
    }

    first_priority = priority[:index]
    second_priority = priority[index + 1 :]
    
    print(first_priority, second_priority)

    results = sorted(
        results.values(),
        key=lambda x: tuple([x[mapping_priority[p]] for p in first_priority]),
        reverse=True,
    )

    temp = []
    groups = []

    for i in range(len(results)):
        if i == 0 or all(
            results[i][mapping_priority[p]] == results[i - 1][mapping_priority[p]]
            for p in first_priority
        ):
            temp.append(results[i])
        else:
            groups.append(temp)
            temp = [results[i]]

    # for each group, sort with second_priority
    for group in groups:
        group = sorted(
            group,
            key=lambda x: tuple([x[mapping_priority[p]] for p in second_priority]),
            reverse=True,
        )

    results = [item for sublist in groups for item in sublist]

    return results
