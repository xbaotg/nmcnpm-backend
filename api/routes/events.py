from datetime import date, time, datetime

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func, or_

from api.deps import CurrentUser, List
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Matches, Events, GoalTypes
from schemas.events import EventAdd

from utils import is_admin, check_event_time, convert_from_attr, count_goals

# from utils import

route = APIRouter()


@route.get("/")
async def default(db: db_deps):
    db_events = db.query(Events).filter(Events.show == True).all()
    return db_events


@route.post("/add-event")
async def add_event(db: db_deps, current_user: CurrentUser, event: EventAdd):
    is_admin(db, current_user)
    # check valid match
    match = (
        db.query(Matches)
        .filter(Matches.show == True, Matches.match_id == event.match_id)
        .first()
    )
    if not match:
        raise HTTPException(status_code=400, detail="Can't find match!")
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
        raise HTTPException(status_code=400, detail="Can't find player!")

    # check time of event in (max_goal_time)

    try:
        event_time = datetime.strptime(event.minute_event, f"%H:%M")
        event_time = datetime.strftime(event_time, f"%H:%M")
    except:
        raise HTTPException(status_code=400, detail="Invalid event time!")

    check_event_time(db, event_time)

    # check valid events name

    event_name = convert_from_attr(
        GoalTypes, event.event_name, "type_name", "type_id", True
    )
    if not event_name:
        raise HTTPException(status_code=400, detail="Invalid event name!")

    # check duplicate
    dup = (
        db.query(Events)
        .filter(
            Events.show == True,
            or_(
                Events.match_id == event.match_id,
                Events.player_id == event.player_id,
                Events.minute_event == datetime.strptime(event_time, "%H:%M").time(),
            ),
            or_(Events.minute_event == datetime.strptime(event_time, "%H:%M").time()),
        )
        .first()
    )

    if dup:
        raise HTTPException(status_code=400, detail=f"Duplicated event!")

    # if no conflict -> add
    new_event = Events(
        match_id=event.match_id,
        events=event.event_name.upper(),
        minute_event=event_time,
        player_id=event.player_id,
        show=True,
    )

    print(event_time)
    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return {"message": "Add event successfully!"}, new_event


# DELETE
@route.put("/delete")
async def delete_event(db: db_deps, current_user: CurrentUser, id: int, time: str):
    is_admin(db, current_user)
    target = (
        db.query(Events)
        .filter(
            Events.show == True,
            Events.minute_event == datetime.strptime(time, "%H:%M"),
            Events.match_id == id,
        )
        .first()
    )
    if not target:
        return {"message": "Can't find event"}

    target.show == False

    db.commit()
    db.refresh(target)
    return {"message": "Deleted successfully"}


@route.put("/restore")
async def restore_event(db: db_deps, current_user: CurrentUser, id: int, time: str):
    is_admin(db, current_user)
    target = (
        db.query(Events)
        .filter(
            Events.show == False,
            Events.minute_event == datetime.strptime(time, "%H:%M"),
            Events.match_id == id,
        )
        .first()
    )
    if not target:
        return {"message": "Can't find event"}

    target.show == True

    db.commit()
    db.refresh(target)
    return {"message": "Restored successfully"}


@route.get("/count")
async def count_goals_of_match(db: db_deps, current_user: CurrentUser, id: int):
    is_admin(db, current_user)
    goal1, goal2 = count_goals(db, id)
    return goal1, goal2
