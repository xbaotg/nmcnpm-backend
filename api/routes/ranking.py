from datetime import datetime
from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

# from api.deps import get_db
from core.db import db_deps
from schemas.db import Clubs, Matches, Params, Ranking
from schemas.ranking import Criteria, RankingRes
from utils import get_params, datetime_to_unix

route = APIRouter()


def create_RankingRes(db: Session, r: Ranking) -> RankingRes:
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
    next_match_id = next_match.match_id if next_match else None

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

    return RankingRes(
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


@route.get("/ranking")
async def ranking(db: db_deps, crit: Criteria, desc: bool = True):
    try:
        if crit == "points":
            order = Ranking.club_points.desc() if desc else Ranking.club_points.asc()
        elif crit == "goals":
            order = Ranking.club_goals.desc() if desc else Ranking.club_goals.asc()
        elif crit == "away_goals":
            order = Ranking.away_goals.desc() if desc else Ranking.away_goals.asc()
        elif crit == "gdif":
            order = Ranking.club_gdif.desc() if desc else Ranking.club_gdif.asc()
        elif crit == "win":
            order = Ranking.club_win.desc() if desc else Ranking.club_win.asc()
        elif crit == "draw":
            order = Ranking.club_draw.desc() if desc else Ranking.club_draw.asc()
        elif crit == "lost":
            order = Ranking.club_lost.desc() if desc else Ranking.club_lost.asc()
        else:
            raise HTTPException(status_code=400, detail="Invalid criteria")

        rankings = db.query(Ranking).filter(Ranking.show == True).order_by(order).all()
        res = [create_RankingRes(db, ranking) for ranking in rankings]

        return {
            "status": "success",
            "message": "Rankings retrieved successfully",
            "data": res,
        }
    except HTTPException as e:
        return {"status": "error", "message": str(e.detail)}
    except Exception as e:
        return {
            "status": "error",
            "message": "An error occurred while retrieving rankings",
        }


@route.get("/init-rank")
async def init_rank(db: db_deps):
    try:
        clubs = (
            db.query(Clubs)
            .filter(Clubs.show == True)
            .order_by(Clubs.club_id.desc())
            .all()
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

        return {
            "status": "success",
            "message": "Ranking initialized successfully",
            "data": ranks,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "An error occurred while initializing ranking",
        }


@route.put("/update-values")
async def update_ranking_values(db: db_deps):
    try:
        matches = (
            db.query(Matches).filter(Matches.show == True, Matches.finish != None).all()
        )

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

        params = get_params(Params, db)

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

            rank_club1.club_goals = (rank_club1.club_goals or 0) + match.goal1
            rank_club2.club_goals = (rank_club2.club_goals or 0) + match.goal2

            rank_club2.away_goals = (rank_club2.away_goals or 0) + match.goal2

            if match.goal1 == match.goal2:
                rank_club1.club_draw = (rank_club1.club_draw or 0) + 1
                rank_club2.club_draw = (rank_club2.club_draw or 0) + 1
            elif match.goal1 < match.goal2:
                rank_club1.club_lost = (rank_club1.club_lost or 0) + 1
                rank_club2.club_win = (rank_club2.club_win or 0) + 1
            else:
                rank_club1.club_win = (rank_club1.club_win or 0) + 1
                rank_club2.club_lost = (rank_club2.club_lost or 0) + 1

            rank_club1.club_gconcede += match.goal2
            rank_club2.club_gconcede += match.goal1

            db.commit()

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

            rank_club1.club_gdif = (
                (rank_club1.club_gdif or 0) + match.goal1 - match.goal2
            )
            rank_club2.club_gdif = (
                (rank_club2.club_gdif or 0) + match.goal2 - match.goal1
            )

        return {"status": "success", "message": "Ranking values updated successfully"}
    except Exception as e:
        return {
            "status": "error",
            "message": "An error occurred while updating ranking values",
        }


# @route.get("/rank-with-priority")
# async def rank_with_priority(
#     db: db_deps,
#     crit1: Criteria,
#     crit5: Criteria = Criteria.none,
#     crit2: Criteria = Criteria.none,
#     crit3: Criteria = Criteria.none,
#     crit4: Criteria = Criteria.none,
#     desc: bool = True,
# ):
#     try:
#         crit1 = str(crit1).replace("Criteria.", "")
#         crit2 = str(crit2).replace("Criteria.", "")
#         crit3 = str(crit3).replace("Criteria.", "")
#         crit4 = str(crit4).replace("Criteria.", "")
#         crit5 = str(crit5).replace("Criteria.", "")

#         if crit2 == "none":
#             crit2 = crit1
#         if crit3 == "none":
#             crit3 = crit1
#         if crit4 == "none":
#             crit4 = crit1
#         if crit5 == "none":
#             crit5 = crit1

#         query = db.query(Ranking).filter(Ranking.show == True)

#         if desc:
#             query = query.order_by(
#                 getattr(Ranking, crit1).desc(),
#                 getattr(Ranking, crit2).desc(),
#                 getattr(Ranking, crit3).desc(),
#                 getattr(Ranking, crit4).desc(),
#                 getattr(Ranking, crit5).desc(),
#             )
#         else:
#             query = query.order_by(
#                 getattr(Ranking, crit1),
#                 getattr(Ranking, crit2),
#                 getattr(Ranking, crit3),
#                 getattr(Ranking, crit4),
#                 getattr(Ranking, crit5),
#             )

#         results = query.all()

#         return {
#             "status": "success",
#             "message": "Rankings with priority retrieved successfully",
#             "data": results,
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": "An error occurred while retrieving rankings with priority",
#         }


@route.get("/get")
async def rank_baotg(db: db_deps):
    try:
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
                results[club.club_id]["club_win"] * 3
                + results[club.club_id]["club_draw"]
            )
            results[club.club_id]["club_gdif"] = (
                results[club.club_id]["club_goals"]
                - results[club.club_id]["club_gconcede"]
            )

        index = priority.index("h")

        mapping_priority = {
            "p": "club_points",
            "d": "club_gdif",
            "g": "club_goals",
        }

        first_priority = priority[:index]
        second_priority = priority[index + 1 :]

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

        if temp:
            groups.append(temp)

        for group in groups:
            group.sort(
                key=lambda x: tuple([x[mapping_priority[p]] for p in second_priority]),
                reverse=True,
            )

        sorted_results = [item for sublist in groups for item in sublist]

        return {
            "status": "success",
            "message": "Ranking retrieved successfully",
            "data": sorted_results,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "An error occurred while retrieving the ranking",
        }
