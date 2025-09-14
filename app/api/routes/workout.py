from fastapi import APIRouter, Depends, HTTPException
from app.api.utils.db import users_collection
from app.api.utils.auth import decode_access_token
from fastapi import Header
import app.api.utils.state as state
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.post("/save")
async def save_workout(
    workout: dict,
    Authorization: str = Header(None)
):
    """
    Save a workout (squat, pushup, rest, etc.) to the logged-in user's workouts array.
    """
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = Authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("username")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid user in token")

    if "persona" not in workout:
        workout["persona"] = state.PERSONA or "default"

    await users_collection.update_one(
        {"username": username},
        {"$push": {"workouts": workout}}
    )

    return {"status": "ok", "msg": "Workout saved", "workout": workout}


router = APIRouter(prefix="/workouts", tags=["workouts"])

@router.post("/flush")
async def flush_workouts(user: dict = Depends(get_current_user)):
    if not state.WORKOUTS_BUFFER:
        return {"status": "empty", "msg": "No workouts to save"}

    await users_collection.update_one(
        {"username": user["username"]},
        {"$push": {"workouts": {"$each": state.WORKOUTS_BUFFER}}}
    )

    saved_count = len(state.WORKOUTS_BUFFER)
    state.WORKOUTS_BUFFER.clear()
    return {"status": "ok", "saved": saved_count}