import time
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from app.api.utils.db import users_collection
from app.api.utils.auth import decode_access_token
import app.api.utils.state as state
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/workouts", tags=["workouts"])


def format_timestamp(ts: float) -> str:

    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


@router.post("/save")
async def save_workout(
    workout: dict,
    Authorization: str = Header(None)
):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = Authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid user in token")

    workout.setdefault("persona", state.PERSONA or "default")
    workout.setdefault("created_at", time.time())

    await users_collection.update_one(
        {"username": username},
        {"$push": {"workouts": workout}}
    )
    return {
        "status": "ok",
        "msg": "Workout saved",
        "workout": {
            **workout,
            "created_at_human": format_timestamp(workout["created_at"])
        }
    }


@router.post("/flush")
async def flush_workouts(user: dict = Depends(get_current_user)):
 
    if not state.WORKOUTS_BUFFER:
        return {"status": "empty", "msg": "No workouts to save"}

    for w in state.WORKOUTS_BUFFER:
        w.setdefault("created_at", time.time())
        w.setdefault("persona", state.PERSONA or "default")

    await users_collection.update_one(
        {"username": user["username"]},
        {"$push": {"workouts": {"$each": state.WORKOUTS_BUFFER}}}
    )

    saved = [
        {**w, "created_at_human": format_timestamp(w["created_at"])}
        for w in state.WORKOUTS_BUFFER
    ]

    saved_count = len(state.WORKOUTS_BUFFER)
    state.WORKOUTS_BUFFER.clear()

    return {"status": "ok", "saved": saved_count, "workouts": saved}
