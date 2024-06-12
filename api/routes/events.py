from fastapi import APIRouter, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from api.deps import CurrentUser
from core.db import db_deps
from schemas.db import Clubs, Players, Users, Params, Matches, Events, GoalTypes
from schemas.events import EventAdd, EventUpdate

from utils import (
    is_admin,
    check_event_time,
    convert_from_attr,
    count_goals,
    to_second,
    update_match,
)

route = APIRouter()


@route.get("/")
async def default(db: db_deps):
    db_events = db.query(Events).filter(Events.show == True).all()
    return {
        "status": "success",
        "message": "Events retrieved successfully",
        "data": db_events,
    }


@route.get("/get-events-of-match")
async def get_events_of_match(db: db_deps, match_id: int):
    events = (
        db.query(Events).filter(Events.show == True, Events.match_id == match_id).all()
    )

    if not events:
        return {
            "status": "success",
            "message": "No events found for this match",
            "data": [],
        }

    return {
        "status": "success",
        "message": "Events retrieved successfully",
        "data": events,
    }


@route.post("/add")
async def add_event(
    db: db_deps,
    current_user: CurrentUser,
    event: EventAdd,
):
    is_admin(db, current_user)

    match = (
        db.query(Matches)
        .filter(Matches.show == True, Matches.match_id == event.match_id)
        .first()
    )

    if not match:
        return {
            "status": "error",
            "message": "Can't find match!",
        }

    # check valid player
    player = (
        db.query(Players)
        .filter(
            Players.show == True,
            Players.player_id == event.player_id,
            or_(Players.player_club == match.team1, Players.player_club == match.team2),
        )
        .first()
    )

    if not player:
        return {
            "status": "error",
            "message": "Can't find player!",
        }

    # Check team_id == player.player_club
    if not (event.team_id == player.player_club):
        return {
            "status": "error",
            "message": "The player is not in this team ID!",
        }

    res = check_event_time(db, event.seconds)
    print(res)
    
    if "status" in res and res["status"] == "error":
        return res

    event_name = convert_from_attr(
        GoalTypes, event.events, "type_name", "type_id", True
    )
    if not event_name:
        return {
            "status": "error",
            "message": "Invalid event name!",
        }

    # check duplicate
    dup = (
        db.query(Events)
        .filter(
            Events.show == True,
            Events.match_id == event.match_id,
            Events.seconds == event.seconds,
        )
        .first()
    )

    if dup:
        return {
            "status": "error",
            "message": "Duplicated event!",
        }

    # if no conflict -> add
    new_event = Events(
        event_id=1 + (db.query(func.max(Events.event_id)).scalar() or 0),
        match_id=event.match_id,
        events=event.events.upper(),
        seconds=event.seconds,
        player_id=event.player_id,
        team_id=event.team_id,
        show=True,
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    # update match
    update_match(db, match.match_id)

    return {
        "status": "success",
        "message": "Add event successfully!",
        "data": new_event,
    }


# update
@route.put("/update")
def update_event(
    db: db_deps,
    current_user: CurrentUser,
    event: EventUpdate,
):
    is_admin(db, current_user)

    target = (
        db.query(Events)
        .filter(
            Events.show == True,
            Events.event_id == event.event_id,
        )
        .first()
    )

    if not target:
        return {
            "status": "error",
            "message": "Can't find event",
        }

    match = (
        db.query(Matches)
        .filter(Matches.show == True, Matches.match_id == event.match_id)
        .first()
    )

    if not match:
        return {
            "status": "error",
            "message": "Can't find match!",
        }

    # check valid player
    player = (
        db.query(Players)
        .filter(
            Players.show == True,
            Players.player_id == event.player_id,
            or_(Players.player_club == match.team1, Players.player_club == match.team2),
        )
        .first()
    )

    if not player:
        return {
            "status": "error",
            "message": "Can't find player!",
        }

    # Check team_id == player.player_club
    if not (event.team_id == player.player_club):
        return {
            "status": "error",
            "message": "The player is not in this team ID!",
        }

    res = check_event_time(db, event.seconds)
    
    if "status" in res and res["status"] == "error":
        return res

    event_name = convert_from_attr(
        GoalTypes, event.events, "type_name", "type_id", True
    )

    if not event_name:
        return {
            "status": "error",
            "message": "Invalid event name!",
        }

    # check duplicate
    target.match_id = event.match_id
    target.events = event.events
    target.seconds = event.seconds
    target.player_id = event.player_id
    target.team_id = event.team_id

    db.commit()
    db.refresh(target)

    # update match
    update_match(db, match.match_id)

    return {
        "status": "success",
        "message": "Updated successfully",
        "data": target,
    }


# DELETE
@route.put("/delete")
async def delete_event(
    db: db_deps,
    current_user: CurrentUser,
    event_id: int,
):
    is_admin(db, current_user)

    target = (
        db.query(Events)
        .filter(
            Events.show == True,
            Events.event_id == event_id,
        )
        .first()
    )
    if not target:
        return {
            "status": "error",
            "message": "Can't find event",
        }

    target.show = False

    db.commit()
    db.refresh(target)

    # update match
    update_match(db, target.match_id)

    return {
        "status": "success",
        "message": "Deleted successfully",
        "data": target,
    }


# DELETE from DATABASE
@route.put("/delete-permanently")
async def delete_event_permanently(
    db: db_deps,
    current_user: CurrentUser,
    event_id: int,
):
    is_admin(db, current_user)
    target = (
        db.query(Events)
        .filter(Events.event_id == event_id, Events.show == False)
        .first()
    )
    if not target:
        return {
            "status": "error",
            "message": "Can't find event",
        }

    db.delete(target)
    db.commit()
    return {
        "status": "success",
        "message": "Deleted permanently successfully",
        "data": target,
    }


@route.put("/restore")
async def restore_event(
    db: db_deps,
    current_user: CurrentUser,
    event_id: int,
):
    is_admin(db, current_user)
    target = (
        db.query(Events)
        .filter(
            Events.show == False,
            Events.event_id == event_id,
        )
        .first()
    )
    if not target:
        return {
            "status": "error",
            "message": "Can't find event",
        }

    target.show = True

    db.commit()
    db.refresh(target)
    return {
        "status": "success",
        "message": "Restored successfully",
        "data": target,
    }


@route.get("/count")
async def count_goals_of_match(
    db: db_deps,
    current_user: CurrentUser,
    id: int,
):
    is_admin(db, current_user)
    goal1, goal2 = count_goals(db, id)
    return {
        "status": "success",
        "message": "Goals counted successfully",
        "data": {"goal1": goal1, "goal2": goal2},
    }
