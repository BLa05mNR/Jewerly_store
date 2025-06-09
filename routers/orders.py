from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
from database import get_db_pool
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["Orders"])


# 📦 Схемы
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class OrderItemOut(BaseModel):
    item_id: int
    order_id: int
    product_id: int
    product_name: str  # Добавлено
    article: str       # Добавлено
    quantity: int
    price: float

# 🔹 Модель заказа с товарами
class OrderCreate(BaseModel):
    client_id: int
    status: str
    items: List[OrderItemCreate]


class OrderOut(BaseModel):
    order_id: int
    username: str
    order_date: datetime
    status: str


class OrderDetailOut(OrderOut):
    items: List[OrderItemOut]

class OrderStatusUpdate(BaseModel):
    status: str

# 📄 Получить все заказы
@router.get("/get/all", response_model=List[OrderOut])
async def get_orders(db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        rows = await connection.fetch("""
            SELECT o.*, u.username
            FROM orders o
            JOIN users u ON o.client_id = u.user_id
            ORDER BY o.order_id
        """)
        return [dict(row) for row in rows]

# 🔎 Получить заказ по ID
@router.get("/get/{order_id}", response_model=OrderDetailOut)
async def get_order(order_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        order = await connection.fetchrow("""
            SELECT o.*, u.username
            FROM orders o
            JOIN users u ON o.client_id = u.user_id
            WHERE o.order_id = $1
        """, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        items = await connection.fetch("""
            SELECT
                oi.*,
                p.price,
                p.name as product_name,
                p.article
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = $1
        """, order_id)

        items_list = []
        for item in items:
            item_dict = dict(item)
            items_list.append({
                "item_id": item_dict["item_id"],
                "order_id": item_dict["order_id"],
                "product_id": item_dict["product_id"],
                "product_name": item_dict["product_name"],
                "article": item_dict["article"],
                "quantity": item_dict["quantity"],
                "price": item_dict["price"]
            })

        return {
            **dict(order),
            "items": items_list
        }

# ➕ Создать заказ с товарами
@router.post("/create")
async def create_order(order: OrderCreate, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        async with connection.transaction():
            try:
                # 1. Создаём заказ и получаем order_id
                order_row = await connection.fetchrow("""
                    INSERT INTO orders (client_id, order_date, status)
                    VALUES ($1, NOW(), $2)
                    RETURNING order_id
                """, order.client_id, order.status)
                order_id = order_row["order_id"]
                logger.info(f"Order created with ID: {order_id}")

                # 2. Добавляем все товары к заказу
                for item in order.items:
                    await connection.execute("""
                        INSERT INTO order_items (order_id, product_id, quantity)
                        VALUES ($1, $2, $3)
                    """, order_id, item.product_id, item.quantity)
                    logger.info(
                        f"Added item to order {order_id}: product_id={item.product_id}, quantity={item.quantity}")

                return {"message": "Order created successfully", "order_id": order_id}

            except Exception as e:
                logger.error(f"Error creating order: {e}")
                raise HTTPException(status_code=500, detail="Internal Server Error")


# ❌ Удалить заказ
@router.delete("/{order_id}")
async def delete_order(order_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        result = await connection.execute("DELETE FROM orders WHERE order_id = $1", order_id)
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Order not found")
        return {"message": "Order deleted"}


# 👤 Клиентские заказы
@router.get("/client/{client_id}", response_model=List[OrderOut])
async def get_client_orders(client_id: int, db=Depends(get_db_pool)):
    """Получить все заказы конкретного клиента"""
    async with db.acquire() as connection:
        rows = await connection.fetch("""
            SELECT o.*, u.username
            FROM orders o
            JOIN users u ON o.client_id = u.user_id
            WHERE o.client_id = $1
            ORDER BY o.order_date DESC
        """, client_id)
        return [dict(row) for row in rows]


@router.get("/client/{client_id}/{order_id}", response_model=OrderDetailOut)
async def get_client_order(client_id: int, order_id: int, db=Depends(get_db_pool)):
    """Получить конкретный заказ клиента"""
    async with db.acquire() as connection:
        # Проверяем, что заказ принадлежит клиенту и получаем username
        order = await connection.fetchrow("""
            SELECT o.*, u.username
            FROM orders o
            JOIN users u ON o.client_id = u.user_id
            WHERE o.order_id = $1 AND o.client_id = $2
        """, order_id, client_id)

        if not order:
            raise HTTPException(status_code=404, detail="Order not found for this client")

        # Получаем items с полной информацией о продукте
        items = await connection.fetch("""
            SELECT 
                oi.*, 
                p.price,
                p.name as product_name,
                p.article
            FROM order_items oi
            JOIN products p ON oi.product_id = p.product_id
            WHERE oi.order_id = $1
        """, order_id)

        return {
            "order_id": order["order_id"],
            "username": order["username"],
            "order_date": order["order_date"],
            "status": order["status"],
            "items": [dict(item) for item in items]
        }


@router.post("/client/{client_id}/create")
async def create_client_order(client_id: int, order: OrderCreate, db=Depends(get_db_pool)):
    """Создать заказ для конкретного клиента"""
    if order.client_id != client_id:
        raise HTTPException(
            status_code=400,
            detail="Client ID in path and body don't match"
        )

    return await create_order(order, db)


@router.delete("/client/{client_id}/{order_id}")
async def delete_client_order(client_id: int, order_id: int, db=Depends(get_db_pool)):
    """Удалить заказ клиента (проверяя принадлежность)"""
    async with db.acquire() as connection:
        result = await connection.execute(
            "DELETE FROM orders WHERE order_id = $1 AND client_id = $2",
            order_id, client_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Order not found or doesn't belong to client")
        return {"message": "Order deleted successfully"}


@router.patch("/{order_id}/status", response_model=OrderOut)
async def update_order_status(order_id: int, status_update: OrderStatusUpdate, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        # Обновляем статус заказа
        updated_order = await connection.fetchrow("""
            UPDATE orders
            SET status = $1
            WHERE order_id = $2
            RETURNING order_id, client_id, order_date, status
        """, status_update.status, order_id)

        if not updated_order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Получаем имя пользователя для ответа
        username_row = await connection.fetchrow("""
            SELECT username FROM users WHERE user_id = $1
        """, updated_order['client_id'])

        if not username_row:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "order_id": updated_order['order_id'],
            "username": username_row['username'],
            "order_date": updated_order['order_date'],
            "status": updated_order['status']
        }