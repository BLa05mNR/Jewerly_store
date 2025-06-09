from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
from database import get_db_pool

router = APIRouter(prefix="/inventory", tags=["Inventory"])

# 📦 Схемы
class InventoryItemCreate(BaseModel):
    product_id: int
    quantity: int

class InventoryItemUpdate(BaseModel):
    quantity: int

class InventoryOut(BaseModel):
    inventory_id: int
    product_id: int
    quantity: int
    updated_at: datetime

# 📄 Получить весь инвентарь
@router.get("/", response_model=List[InventoryOut])
async def get_inventory(db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        rows = await connection.fetch("SELECT * FROM inventory ORDER BY inventory_id")
        return [dict(row) for row in rows]

# 🔎 Получить запись инвентаря по ID
@router.get("/{inventory_id}", response_model=InventoryOut)
async def get_inventory_item(inventory_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow("SELECT * FROM inventory WHERE inventory_id = $1", inventory_id)
        if not row:
            raise HTTPException(status_code=404, detail="Inventory item not found")
        return dict(row)

# 🔎 Получить запись инвентаря по product_id
@router.get("/product/{product_id}", response_model=InventoryOut)
async def get_inventory_by_product(product_id: int, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow("SELECT * FROM inventory WHERE product_id = $1", product_id)
        if not row:
            raise HTTPException(status_code=404, detail="Inventory item for this product not found")
        return dict(row)

# ➕ Создать запись в инвентаре
@router.post("/", response_model=InventoryOut)
async def create_inventory_item(item: InventoryItemCreate, db=Depends(get_db_pool)):
    async with db.acquire() as connection:
        row = await connection.fetchrow("""
            INSERT INTO inventory (product_id, quantity, updated_at)
            VALUES ($1, $2, NOW())
            RETURNING *
        """, item.product_id, item.quantity)
        return dict(row)
