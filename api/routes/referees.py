from datetime import date

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fuzzywuzzy import fuzz
from sqlalchemy import func

from api.deps import CurrentUser, List
from core.db import db as code_db
from core.db import db_deps
from schemas.db import Referees, Clubs, Players, Users
from schemas.referees import RefCreate, RefShow, RefUpdate

route = APIRouter()


def get_user_permission(db: db_deps, current_user: CurrentUser, role: str):
    if current_user is None:
        raise HTTPException(
            status_code=401,
            detail={"status": "error", "message": "Authentication Failed"},
        )

    user_role = (
        db.query(Users).filter(Users.user_id == current_user["user_id"]).first().role  # type: ignore
    )

    # check permission of user_role
    if role == "manager":
        # check if user is deleted or not
        if (
            not db.query(Users)
            .filter(Users.user_id == current_user["user_id"])
            .first()
            .show  # type: ignore
        ):
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "error",
                    "message": "Your account is no longer active!",
                },
            )

        return True
    elif role == "admin" and user_role != role:
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "You don't have permission to do this action!",
            },
        )

    return True


@route.post("/add-refs")
async def add_refs(ref: RefCreate, db: db_deps):  # current_user: CurrentUser):
    try:
        # hasPermission = get_user_permission(current_user, db, "admin")
        newRefDict = ref.dict()
        for key, value in newRefDict.items():
            if value == "string":
                return {"status": "error", "message": f"{key} is required."}

        count = db.query(func.max(Referees.ref_id)).scalar()
        newRefDict["ref_id"] = (count or 0) + 1
        new_db_ref = Referees(**newRefDict)

        db.add(new_db_ref)
        db.commit()
        db.refresh(new_db_ref)
        return {
            "status": "success",
            "message": "Referee added successfully",
            "data": new_db_ref,
        }

    except HTTPException as e:
        db.rollback()
        raise e

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Internal Server Error: {str(e)}"},
        )


@route.get("/get-ref")
async def get_ref(ref_name: str, db: db_deps, threshold: int = 80):
    try:
        refs = db.query(Referees).filter(Referees.show == True).all()
        matched_refs = [
            ref
            for ref in refs
            if fuzz.partial_ratio(ref.ref_name.lower(), ref_name.lower()) >= threshold
        ]

        if not matched_refs:
            raise HTTPException(
                status_code=204,
                detail={"status": "error", "message": "Cannot find ref"},
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Internal Server Error: {str(e)}"},
        )
    return {
        "status": "success",
        "message": "Referees fetched successfully",
        "data": matched_refs,
    }


@route.get("/get-all")
async def get_all_refs(db: db_deps):
    try:
        refs = db.query(Referees).filter(Referees.show == True).all()
        if not refs:
            raise HTTPException(
                status_code=204, detail={"status": "error", "message": "No refs found"}
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Internal Server Error: {str(e)}"},
        )

    return {
        "status": "success",
        "message": "All referees fetched successfully",
        "data": refs,
    }


@route.put("/update-ref")
async def update_ref(
    ref_id: int, ref_update: RefUpdate, db: db_deps
):  # current_user: CurrentUser):
    try:
        # hasPermission = get_user_permission(current_user, db, "manager")
        target = db.query(Referees).filter(Referees.ref_id == ref_id).first()
        update_info = ref_update.dict(exclude_unset=True)
        for key, value in update_info.items():
            if value == "string":
                return {"status": "error", "message": f"{key} is required."}
            setattr(target, key, value)
        db.commit()
        db.refresh(target)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Internal Server Error: {str(e)}!"},
        )
    return {
        "status": "success",
        "message": "Referee updated successfully",
        "data": target,
    }


@route.put("/delete-ref")
async def delete_ref(ref_id: int, current_user: CurrentUser, db: db_deps):
    hasPermission = get_user_permission(db, current_user, "admin")

    try:
        target = db.query(Referees).filter(Referees.ref_id == ref_id).first()

        if target is None:
            raise HTTPException(
                status_code=204,
                detail={
                    "status": "error",
                    "message": f"Can't find ref with id:{ref_id}",
                },
            )

        if target.show == True:
            target.show = False
            db.commit()
            return {"status": "success", "message": f"Deleted ref with id:{ref_id}"}
        else:
            return {
                "status": "error",
                "message": f"Can't find ref with id:{ref_id}. Maybe deleted.",
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Internal Server Error: {str(e)} !"},
        )


@route.put("/restore-deleted-ref")
async def restore_deleted_ref(ref_id: int, current_user: CurrentUser, db: db_deps):
    hasPermission = get_user_permission(db, current_user, "manager")
    try:
        target = db.query(Referees).filter(Referees.ref_id == ref_id).first()
        if target.show != True:
            target.show = True
            db.commit()
            return {"status": "success", "message": f"Restored ref with id:{ref_id}"}
        else:
            return {"status": "error", "message": f"Can't find ref with id:{ref_id}."}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Internal Server Error: {str(e)} !"},
        )


@route.delete("/permanently-delete-ref")
async def permanently_delete_ref(ref_id: int, db: db_deps, current_user: CurrentUser):
    hasPermission = get_user_permission(db, current_user, "manager")

    try:
        target = db.query(Referees).filter(Referees.ref_id == ref_id).first()

        if target is None:
            raise HTTPException(
                status_code=204,
                detail={
                    "status": "error",
                    "message": f"Can't find ref with id:{ref_id}",
                },
            )

        db.delete(target)
        db.commit()

        return {
            "status": "success",
            "message": f"Delete refs with id {ref_id} successfully !",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "message": f"Internal Server Error: {str(e)} !"},
        )
