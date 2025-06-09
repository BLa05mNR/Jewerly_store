from fastapi import APIRouter, Depends, HTTPException, Form
from jose import jwt
from datetime import datetime, timedelta
import bcrypt
from pydantic import BaseModel

from database import get_db_pool

SECRET_KEY = "C1asdd_f1R0M0UsiwkTlg5QkMCAPM1Iq4JWz-FM7osE"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(tags=["Login"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(login_data: LoginRequest, db_pool=Depends(get_db_pool)):
    username = login_data.username
    password = login_data.password

    async with db_pool.acquire() as connection:
        user = await connection.fetchrow(
            "SELECT user_id, username, password_hash, role FROM users WHERE username = $1", username
        )

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Создаём JWT токен
        token_data = {
            "sub": user["username"],
            "role": user["role"],
            "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        }

        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        return {"username": username, "role": user["role"], "user_id": user["user_id"]}