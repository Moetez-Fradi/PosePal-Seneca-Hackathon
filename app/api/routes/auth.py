from fastapi import APIRouter, HTTPException, Response, Depends, Cookie
from app.api.utils.db import users_collection
from app.api.utils.auth import hash_password, verify_password, create_access_token, decode_access_token
from app.api.models.user import UserSignup


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
def login(response: Response, username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"username": username})
    response.set_cookie(key="access_token", value=token, httponly=True)

    first_time = user.get("persona", "default") == "default"

    return {
        "status": "ok",
        "msg": "Logged in successfully",
        "first_time": first_time 
    }



# ---------- Logout ----------
@router.post("/logout", response_model=dict)
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "ok", "msg": "Logged out"}


# ---------- Dependency ----------
async def get_current_user(access_token: str = Cookie(None)):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = decode_access_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    username = payload.get("username")
    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


# ---------- Dashboard ----------
@router.get("/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    workouts = user.get("workouts", [])
    return {
        "username": user["username"],
        "email": user["email"],
        "persona": user.get("persona", "default"),
        "total_workouts": len(workouts),
        "workouts": workouts
    }


@router.post("/set_persona")
def set_persona(persona: str, user: dict = Depends(get_current_user)):
    if persona not in ["david_goggins", "barbie", "default"]:
        raise HTTPException(status_code=400, detail="Invalid persona choice")

    users_collection.update_one(
        {"username": user["username"]},
        {"$set": {"persona": persona}}
    )
    return {"status": "ok", "msg": f"Persona set to {persona}"}
