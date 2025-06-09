from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db_pool

router = APIRouter(prefix="/returns", tags=["Returns"])


class ReturnBase(BaseModel):
    order_id: int
    client_id: int
    return_date: datetime
    description: str
    status: str


class ReturnCreate(ReturnBase):
    pass


class ReturnOut(ReturnBase):
    return_id: int


class ReturnStatusUpdate(BaseModel):
    status: str


# 📄 Получить все возвраты
@router.get("/get/all/", response_model=List[ReturnOut])
async def get_returns(db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM returns ORDER BY return_id")
        return [dict(row) for row in rows]


# 🔎 Получить возврат по ID
@router.get("/get/{return_id}", response_model=ReturnOut)
async def get_return_by_id(return_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow("SELECT * FROM returns WHERE return_id = $1", return_id)
        if not row:
            raise HTTPException(status_code=404, detail="Return not found")
        return dict(row)


# 👤 Получить возвраты по client_id
@router.get("/get/by-client/{client_id}", response_model=List[ReturnOut])
async def get_returns_by_client(client_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM returns WHERE client_id = $1 ORDER BY return_date DESC", client_id)
        if not rows:
            raise HTTPException(status_code=404, detail="No returns found for this client")
        return [dict(row) for row in rows]


# 🛒 Получить возвраты по order_id
@router.get("/get/by-order/{order_id}", response_model=List[ReturnOut])
async def get_returns_by_order(order_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM returns WHERE order_id = $1 ORDER BY return_date DESC", order_id)
        if not rows:
            raise HTTPException(status_code=404, detail="No returns found for this order")
        return [dict(row) for row in rows]


# ➕ Создать возврат
@router.post("/create", response_model=ReturnOut)
async def create_return(return_data: ReturnCreate, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow("""
            INSERT INTO returns (
                order_id, client_id, return_date, description, status
            ) VALUES (
                $1, $2, $3, $4, $5
            )
            RETURNING *
        """, return_data.order_id, return_data.client_id, return_data.return_date,
                                        return_data.description, return_data.status)
        return dict(row)


# 🔄 Обновить только статус возврата (PATCH)
@router.patch("/update-status/{return_id}", response_model=ReturnOut)
async def update_return_status(
        return_id: int,
        status_update: ReturnStatusUpdate,
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        row = await connection.fetchrow("""
            UPDATE returns
            SET status = $1
            WHERE return_id = $2
            RETURNING *
        """, status_update.status, return_id)
        if not row:
            raise HTTPException(status_code=404, detail="Return not found")
        return dict(row)


# 🗑️ Удалить возврат
@router.delete("/delete/{return_id}")
async def delete_return(return_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        result = await connection.execute("DELETE FROM returns WHERE return_id = $1", return_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Return not found")
        return {"message": "Return deleted successfully"}