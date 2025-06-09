from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from database import get_db_pool

router = APIRouter(prefix="/products", tags=["Products"])


class ProductBase(BaseModel):
    name: str
    article: str
    type: str
    material: str
    insert_type: str
    weight: float
    price: float
    stock_quantity: int
    image_id: int


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    product_id: int
    created_at: datetime


class StockQuantityUpdate(BaseModel):
    amount: int  # Количество для изменения (положительное - увеличение, отрицательное - уменьшение)
    reason: Optional[str] = None  # Причина изменения (например, "продажа", "поступление", "списание")


# 📄 Получить все товары
@router.get("/get/all/", response_model=List[ProductOut])
async def get_products(db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM products ORDER BY product_id")
        return [dict(row) for row in rows]


# 🔎 Получить один товар
@router.get("/get/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow("SELECT * FROM products WHERE product_id = $1", product_id)
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        return dict(row)


# ➕ Создать товар
@router.post("/create", response_model=ProductOut)
async def create_product(product: ProductCreate, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow("""
            INSERT INTO products (
                name, article, type, material, insert_type, weight, price, stock_quantity, image_id, created_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, NOW()
            )
            RETURNING *
        """, product.name, product.article, product.type, product.material,
                                        product.insert_type, product.weight, product.price, product.stock_quantity,
                                        product.image_id)
        return dict(row)


# 🔢 Изменить количество товара (увеличение/уменьшение)
@router.patch("/update-stock/{product_id}", response_model=ProductOut)
async def update_product_stock(
        product_id: int,
        stock_update: StockQuantityUpdate,
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        # Получаем текущее количество товара
        product = await connection.fetchrow(
            "SELECT stock_quantity FROM products WHERE product_id = $1",
            product_id
        )
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        current_quantity = product['stock_quantity']
        new_quantity = current_quantity + stock_update.amount

        # Проверка на отрицательное количество после уменьшения
        if new_quantity < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock. Current: {current_quantity}, attempted to reduce by: {-stock_update.amount}"
            )

        # Обновляем количество
        row = await connection.fetchrow("""
            UPDATE products
            SET stock_quantity = $1
            WHERE product_id = $2
            RETURNING *
        """, new_quantity, product_id)

        # Здесь можно добавить логирование изменения количества
        # await log_stock_change(connection, product_id, stock_update.amount, stock_update.reason)

        return dict(row)


# ➖ Уменьшить количество товара (специальный эндпоинт для уменьшения)
@router.patch("/reduce-stock/{product_id}", response_model=ProductOut)
async def reduce_product_stock(
        product_id: int,
        stock_reduce: StockQuantityUpdate,
        db=Depends(get_db_pool)
):
    # Проверяем что количество для уменьшения положительное
    if stock_reduce.amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Amount to reduce must be positive. Use negative amount in /update-stock for increasing."
        )

    # Преобразуем в отрицательное число для уменьшения
    stock_update = StockQuantityUpdate(
        amount=-stock_reduce.amount,
        reason=stock_reduce.reason
    )

    return await update_product_stock(product_id, stock_update, db)


# ✏️ Обновить информацию о товаре
@router.patch("/update/{product_id}", response_model=ProductOut)
async def update_product(
        product_id: int,
        product_update: ProductBase,
        db=Depends(get_db_pool)
):
    async with db.acquire() as connection:
        row = await connection.fetchrow("""
            UPDATE products
            SET 
                name = $1,
                article = $2,
                type = $3,
                material = $4,
                insert_type = $5,
                weight = $6,
                price = $7,
                stock_quantity = $8,
                image_id = $9
            WHERE product_id = $10
            RETURNING *
        """,
                                        product_update.name,
                                        product_update.article,
                                        product_update.type,
                                        product_update.material,
                                        product_update.insert_type,
                                        product_update.weight,
                                        product_update.price,
                                        product_update.stock_quantity,
                                        product_update.image_id,
                                        product_id)

        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        return dict(row)

# 🗑️ Удалить товар
@router.delete("/delete/{product_id}", response_model=dict)
async def delete_product(product_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        # Проверяем, существует ли продукт
        product = await connection.fetchrow("SELECT product_id FROM products WHERE product_id = $1", product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Удаляем продукт
        await connection.execute("DELETE FROM products WHERE product_id = $1", product_id)

        return {"message": "Product deleted successfully", "product_id": product_id}