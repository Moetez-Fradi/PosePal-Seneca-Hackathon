from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from app.api.utils.db import users_collection
from app.api.utils.auth import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

# ----------------------
# Signup
# ----------------------
@router.post("/signup")
def signup(username: str, password: str, email: str):
    if users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed_pw = hash_password(password)
    user = {"username": username, "password": hashed_pw, "email": email, "workouts": []}
    users_collection.insert_one(user)
    return {"status": "ok", "msg": "User created successfully"}


# ----------------------
# Login
# ----------------------
@router.post("/login")
def login(username: str, password: str):
    user = users_collection.find_one({"username": username})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token
    token = create_access_token({"username": username})
    return {"status": "ok", "msg": "Logged in successfully", "access_token": token}


# ----------------------
# Dependency to get current user
# ----------------------
def get_current_user(authorization: Optional[str] = Header(None)):
    """
    Extract JWT from 'Authorization: Bearer <token>' header
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid auth scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = payload.get("username")
    user = users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# ----------------------
# Dashboard (protected route)
# ----------------------
@router.get("/dashboard")
def dashboard(user: dict = Depends(get_current_user)):
    workouts = user.get("workouts", [])
    for w in workouts:
        if "persona" not in w:
            w["persona"] = "default"  # ensure persona field exists
    return {
        "username": user["username"],
        "email": user["email"],
        "total_workouts": len(workouts),
        "workouts": workouts
    }
