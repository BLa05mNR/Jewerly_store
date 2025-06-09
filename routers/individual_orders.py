from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db_pool

router = APIRouter(prefix="/individual-orders", tags=["Individual Orders"])


class IndividualOrderBase(BaseModel):
    client_id: int
    order_date: datetime
    status: str
    description: str
    total_amount: float
    delivery_address: str
    contact_phone: str


class IndividualOrderCreate(IndividualOrderBase):
    pass


class IndividualOrderOut(IndividualOrderBase):
    order_id: int


class IndividualOrderStatusUpdate(BaseModel):
    status: str


class IndividualOrderUpdate(BaseModel):
    description: Optional[str] = None
    total_amount: Optional[float] = None
    delivery_address: Optional[str] = None
    contact_phone: Optional[str] = None
    status: Optional[str] = None


# 📄 Получить все индивидуальные заказы
@router.get("/get/all/", response_model=List[IndividualOrderOut])
async def get_all_individual_orders(
        status: Optional[str] = Query(None, description="Фильтр по статусу"),
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        if status:
            rows = await connection.fetch(
                "SELECT * FROM individual_orders WHERE status = $1 ORDER BY order_date DESC",
                status
            )
        else:
            rows = await connection.fetch(
                "SELECT * FROM individual_orders ORDER BY order_date DESC"
            )
        return [dict(row) for row in rows]


# 🔎 Получить заказ по ID
@router.get("/get/{order_id}", response_model=IndividualOrderOut)
async def get_individual_order_by_id(order_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow(
            "SELECT * FROM individual_orders WHERE order_id = $1",
            order_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Individual order not found")
        return dict(row)


# 👤 Получить заказы по client_id
@router.get("/get/by-client/{client_id}", response_model=List[IndividualOrderOut])
async def get_individual_orders_by_client(
        client_id: int,
        status: Optional[str] = Query(None, description="Фильтр по статусу"),
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        if status:
            rows = await connection.fetch(
                "SELECT * FROM individual_orders WHERE client_id = $1 AND status = $2 ORDER BY order_date DESC",
                client_id, status
            )
        else:
            rows = await connection.fetch(
                "SELECT * FROM individual_orders WHERE client_id = $1 ORDER BY order_date DESC",
                client_id
            )
        if not rows:
            raise HTTPException(
                status_code=404,
                detail="No individual orders found for this client"
            )
        return [dict(row) for row in rows]


# ➕ Создать индивидуальный заказ
@router.post("/create", response_model=IndividualOrderOut)
async def create_individual_order(
        order_data: IndividualOrderCreate,
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        row = await connection.fetchrow("""
            INSERT INTO individual_orders (
                client_id, order_date, status, description, 
                total_amount, delivery_address, contact_phone
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7
            )
            RETURNING *
        """,
                                        order_data.client_id, order_data.order_date, order_data.status,
                                        order_data.description, order_data.total_amount,
                                        order_data.delivery_address, order_data.contact_phone)
        return dict(row)


# 🔄 Обновить статус заказа (PATCH)
@router.patch("/update-status/{order_id}", response_model=IndividualOrderOut)
async def update_individual_order_status(
        order_id: int,
        status_update: IndividualOrderStatusUpdate,
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        row = await connection.fetchrow("""
            UPDATE individual_orders
            SET status = $1
            WHERE order_id = $2
            RETURNING *
        """, status_update.status, order_id)
        if not row:
            raise HTTPException(status_code=404, detail="Individual order not found")
        return dict(row)


# ✏️ Обновить данные заказа (PATCH)
@router.patch("/update/{order_id}", response_model=IndividualOrderOut)
async def update_individual_order(
        order_id: int,
        order_update: IndividualOrderUpdate,
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        # Собираем только те поля, которые были переданы для обновления
        update_fields = {}
        if order_update.description is not None:
            update_fields['description'] = order_update.description
        if order_update.total_amount is not None:
            update_fields['total_amount'] = order_update.total_amount
        if order_update.delivery_address is not None:
            update_fields['delivery_address'] = order_update.delivery_address
        if order_update.contact_phone is not None:
            update_fields['contact_phone'] = order_update.contact_phone
        if order_update.status is not None:
            update_fields['status'] = order_update.status

        if not update_fields:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        set_clause = ", ".join([f"{field} = ${i + 1}" for i, field in enumerate(update_fields.keys())])
        values = list(update_fields.values())
        values.append(order_id)

        row = await connection.fetchrow(f"""
            UPDATE individual_orders
            SET {set_clause}
            WHERE order_id = ${len(update_fields) + 1}
            RETURNING *
        """, *values)

        if not row:
            raise HTTPException(status_code=404, detail="Individual order not found")
        return dict(row)


# 🗑️ Удалить индивидуальный заказ
@router.delete("/delete/{order_id}")
async def delete_individual_order(order_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        result = await connection.execute(
            "DELETE FROM individual_orders WHERE order_id = $1",
            order_id
        )
        if result == "DELETE 0":
            raise HTTPException(
                status_code=404,
                detail="Individual order not found"
            )
        return {"message": "Individual order deleted successfully"}