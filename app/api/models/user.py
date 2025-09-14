from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import time


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
    name: str                 # "squat", "pushup", "rest"
    duration: int             # in seconds
    persona: Optional[str] = "default"
    reps: Optional[int] = None
    ended_at: Optional[float] = None
    created_at: float = Field(default_factory=lambda: time.time())


class UserDashboard(BaseModel):
    username: str
    email: EmailStr
    total_workouts: int
    workouts: List[Workout]


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
