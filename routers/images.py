from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from database import get_db_pool

router = APIRouter(prefix="/images", tags=["Images"])

@router.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    pool = await get_db_pool()
    content = await file.read()

    async with pool.acquire() as conn:
        result = await conn.fetchrow("""
            INSERT INTO images (filename, content_type, data)
            VALUES ($1, $2, $3)
            RETURNING image_id
        """, file.filename, file.content_type, content)

    return {"id": result["image_id"], "filename": file.filename}

@router.get("/{image_id}")
async def get_image(image_id: int):
    pool = await get_db_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT filename, content_type, data FROM images WHERE image_id = $1", image_id)
        if not row:
            raise HTTPException(status_code=404, detail="Image not found")

    return StreamingResponse(BytesIO(row["data"]), media_type=row["content_type"], headers={
        "Content-Disposition": f'inline; filename="{row["filename"]}"'
    })
