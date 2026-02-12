from pydantic import BaseModel, EmailStr
from datetime import datetime

# USER
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True

# TOKEN
class Token(BaseModel):
    access_token: str
    token_type: str

# CHAT
class SessionCreate(BaseModel):
    title: str | None = None

class MessageCreate(BaseModel):
    message: str
