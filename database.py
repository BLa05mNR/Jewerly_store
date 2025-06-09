import asyncpg

DATABASE_URL = "postgresql://postgres:0309@localhost:5432/jewerly_store_DB"

async def connect_to_db():
    return await asyncpg.create_pool(DATABASE_URL)

db_pool = None

async def get_db_pool():
    global db_pool
    if db_pool is None:
        db_pool = await connect_to_db()
    return db_pool
