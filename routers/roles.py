from fastapi import APIRouter, Depends
from database import get_db_pool

router = APIRouter()

@router.get("/roles")
async def get_roles(db_pool=Depends(get_db_pool)):
    async with db_pool.acquire() as connection:
        rows = await connection.fetch("SELECT role_id, name FROM roles")
        return [{"role_id": row["role_id"], "name": row["name"]} for row in rows]
