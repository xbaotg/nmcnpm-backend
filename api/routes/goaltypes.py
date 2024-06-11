from fastapi import APIRouter, HTTPException
from sqlalchemy import func, or_

from api.deps import CurrentUser
from core.db import db_deps, Depends
from schemas.db import Clubs, Players, Users, Params, Matches, Events, GoalTypes

from utils import (
    is_admin,
    check_event_time,
)

route = APIRouter()


@route.get("/get")
async def get_goal_types(db: db_deps, current_user: CurrentUser):
    is_admin(db, current_user)

    get = db.query(GoalTypes).filter(GoalTypes.show == True).all()
    return get


@route.post("/add-types")
async def add_types(db: db_deps, current_user: CurrentUser, new_type: str):
    is_admin(db, current_user)

    # check duplicated
    dup = (
        db.query(GoalTypes)
        .filter(GoalTypes.show == True, GoalTypes.type_name == new_type.upper())
        .first()
    )
    if dup:
        raise HTTPException(status_code=400, detail="Duplicated goal type!")

    max_id = db.query(func.max(GoalTypes.type_id)).scalar()
    new_db_type = GoalTypes(
        type_id=(max_id or 0) + 1, type_name=new_type.upper(), show=True
    )

    db.add(new_db_type)
    db.commit()

    return new_db_type


@route.put("/delete-types")
async def delete_types(db: db_deps, current_user: CurrentUser, type_name: str):
    is_admin(db, current_user)

    # find target
    target = (
        db.query(GoalTypes)
        .filter(GoalTypes.show == True, GoalTypes.type_name == type_name.upper())
        .first()
    )
    if not target:
        raise HTTPException(status_code=400, detail="Can't find this type")

    # check if any events is using this type
    event = (
        db.query(Events)
        .filter(Events.show == True, Events.events == type_name.upper())
        .first()
    )

    if event:
        raise HTTPException(
            status_code=405, detail="Can't delete this type, there's an event using it"
        )

    # no conflict -> delete

    target.show = False
    db.commit()


@route.put("/rename-type")
async def rename_type(
    db: db_deps, current_user: CurrentUser, type_name: str, new_name: str
):
    is_admin(db, current_user)

    # find target
    target = (
        db.query(GoalTypes)
        .filter(GoalTypes.show == True, GoalTypes.type_name == type_name.upper())
        .first()
    )
    if not target:
        raise HTTPException(status_code=400, detail="Can't find this type")

    old_name = target.type_name
    target.type_name = new_name.upper()

    # change events name
    events = db.query(Events).filter(Events.events == old_name).all()

    for event in events:
        event.events = new_name.upper()

    db.commit()
