from datetime import datetime
import bcrypt

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import get_db_pool

router = APIRouter(tags=["users"])

class UserCreate(BaseModel):
    username: str
    password: str

class UserAdminCreate(UserCreate):
    role: str

class UserUpdate(BaseModel):
    username: str = None
    password: str = None

@router.get("/users")
async def get_users(db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("""
            SELECT
                u.user_id,
                u.created_at,
                u.username,
                r.name AS role_name
            FROM users u
            JOIN roles r ON u.role = r.role_id
        """)
        return [
            {
                "user_id": row["user_id"],
                "created_at": row["created_at"],
                "username": row["username"],
                "role": row["role_name"]
            } for row in rows
        ]

@router.get("/users/{user_id}")
async def get_user_by_id(user_id: int, db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        row = await connection.fetchrow("""
            SELECT
                u.user_id,
                u.created_at,
                u.username,
                r.name AS role
            FROM users u
            JOIN roles r ON u.role = r.role_id
            WHERE u.user_id = $1
        """, user_id)

        if row is None:
            return {"error": "User not found"}

        return {
            "user_id": row["user_id"],
            "created_at": row["created_at"],
            "username": row["username"],
            "role": row["role"]
        }

@router.get("/users/by-role/{role_name}")
async def get_users_by_role(role_name: str, db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("""
            SELECT
                u.user_id,
                u.created_at,
                u.username,
                r.name AS role
            FROM users u
            JOIN roles r ON u.role = r.role_id
            WHERE r.name = $1
        """, role_name)

        return [
            {
                "user_id": row["user_id"],
                "created_at": row["created_at"],
                "username": row["username"],
                "role": row["role"]
            } for row in rows
        ]

@router.post("/create/users")
async def create_user(user: UserCreate, db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        # Устанавливаем роль по умолчанию равной 5
        default_role = "Клиент"  # Замените на фактическое имя роли
        role_row = await connection.fetchrow(
            "SELECT role_id FROM roles WHERE name = $1", default_role
        )

        if role_row is None:
            raise HTTPException(status_code=400, detail="Default role not found")

        role_id = role_row["role_id"]

        # Хэшируем пароль
        hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        user_id = await connection.fetchval("""
                    INSERT INTO users (username, password_hash, role, created_at)
                    VALUES ($1, $2, $3, $4)
                    RETURNING user_id
                """, user.username, hashed_password, role_id, datetime.utcnow())

        return {"message": "User created successfully", "user_id": user_id}

@router.put("/users/{user_id}")
async def update_user(user_id: int, user_update: UserUpdate, db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        # Check if the user exists
        existing_user = await connection.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Prepare the update query
        update_values = []
        update_query = "UPDATE users SET "

        if user_update.username:
            update_values.append(user_update.username)
            update_query += "username = $1"

        if user_update.password:
            hashed_password = bcrypt.hashpw(user_update.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            update_values.append(hashed_password)
            if user_update.username:
                update_query += ", "
            update_query += "password_hash = $2"

        update_query += " WHERE user_id = $3 RETURNING user_id"
        update_values.append(user_id)

        # Execute the update query
        updated_user_id = await connection.fetchval(update_query, *update_values)

        if updated_user_id is None:
            raise HTTPException(status_code=500, detail="Failed to update user")

        return {"message": "User updated successfully", "user_id": updated_user_id}

@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        # Проверяем, существует ли пользователь
        existing_user = await connection.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user_id)
        if not existing_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Удаляем пользователя
        deleted_user_id = await connection.execute("DELETE FROM users WHERE user_id = $1 RETURNING user_id", user_id)

        if deleted_user_id == "DELETE 0":
            raise HTTPException(status_code=500, detail="Failed to delete user")

        return {"message": "User deleted successfully", "user_id": user_id}

@router.post("/create/admin/users")
async def create_user(user: UserAdminCreate, db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        # Получаем role_id для указанной роли
        role_row = await connection.fetchrow(
            "SELECT role_id FROM roles WHERE name = $1", user.role
        )

        if role_row is None:
            raise HTTPException(status_code=400, detail="Specified role not found")

        role_id = role_row["role_id"]

        # Хэшируем пароль
        hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        # Создаем пользователя с указанной ролью
        user_id = await connection.fetchval("""
            INSERT INTO users (username, password_hash, role, created_at)
            VALUES ($1, $2, $3, $4)
            RETURNING user_id
        """, user.username, hashed_password, role_id, datetime.utcnow())

        return {"message": "User created successfully", "user_id": user_id}