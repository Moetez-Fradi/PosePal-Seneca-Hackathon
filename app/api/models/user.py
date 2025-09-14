from pydantic import BaseModel, EmailStr
from typing import List, Optional


# -------- Request Models --------
class UserSignup(BaseModel):
    username: str
    password: str
    email: EmailStr


class UserLogin(BaseModel):
    username: str
    password: str


# -------- Response Models --------
class Workout(BaseModel):
    name: str
    duration: int
    persona: Optional[str] = "default"


class UserDashboard(BaseModel):
    username: str
    email: EmailStr
    total_workouts: int
    workouts: List[Workout]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
