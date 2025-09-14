from fastapi import APIRouter, HTTPException, Response, Depends, Header
from app.api.utils.db import users_collection
from app.api.utils.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.api.models.user import UserSignup
from pydantic import BaseModel
import app.api.utils.state as state

class LoginRequest(BaseModel):
    username: str
    password: str

class PersonaChoice(BaseModel):
    persona: str

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------- Signup ----------
@router.post("/signup", response_model=dict)
async def signup(user: UserSignup):
    existing = await users_collection.find_one({"username": user.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = hash_password(user.password)
    new_user = {
        "username": user.username,
        "password": hashed_pw,
        "email": user.email,
        "workouts": [],
        "persona": "default"
    }
    await users_collection.insert_one(new_user)
    return {"status": "ok", "msg": "User created successfully"}


# ---------- Login ----------
@router.post("/login")
async def login(data: LoginRequest, response: Response):
    user = await users_collection.find_one({"username": data.username})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"username": data.username})

    first_time = user.get("persona", "default") == "default"
    state.PERSONA = user.get("persona", "default")
    state.CURRENT_USER = data.username

    # ✅ Return token in response (use in frontend with Bearer)
    return {
        "status": "ok",
        "msg": "Logged in successfully",
        "first_time": first_time,
        "access_token": token
    }


# ---------- Dependency ----------
async def get_current_user(Authorization: str = Header(None)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = Authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("username")
    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ---------- Dashboard ----------
@router.get("/dashboard")
async def dashboard(user: dict = Depends(get_current_user)):
    workouts = user.get("workouts", [])
    return {
        "username": user["username"],
        "email": user["email"],
        "persona": user.get("persona", "default"),
        "total_workouts": len(workouts),
        "workouts": workouts
    }


# ---------- Set Persona ----------
@router.post("/set_persona")
async def set_persona(data: PersonaChoice, user: dict = Depends(get_current_user)):
    persona = data.persona
    if persona not in ["goggins", "barbie", "default"]:
        raise HTTPException(status_code=400, detail="Invalid persona choice")

    await users_collection.update_one(
        {"username": user["username"]},
        {"$set": {"persona": persona}}
    )
    state.PERSONA = persona
    return {"status": "ok", "msg": f"Persona set to {persona}"}
