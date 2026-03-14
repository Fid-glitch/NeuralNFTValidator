from fastapi import APIRouter, UploadFile, File, HTTPException
from services import validate_image

router = APIRouter(prefix="/api", tags=["validation"])

@router.post("/validate")
async def validate_nft(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    result = await validate_image(file)
    return result