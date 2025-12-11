from fastapi import APIRouter, HTTPException, Header
from models.autoglm_model import autoglm_model_service
from services.supabase_service import supabase_service
from typing import Optional
from pydantic import BaseModel

router = APIRouter()

class ImageRequest(BaseModel):
    image_url: str
    description: Optional[str] = None

@router.post("/autoglm/infer")
async def autoglm_infer(
    request: ImageRequest,
    authorization: Optional[str] = Header(None)
):
    """
    Generate image caption using BLIP and store result in Supabase.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.replace("Bearer ", "")

    try:
        result = autoglm_model_service.infer(request.image_url)
        
        db_result = supabase_service.create_autoglm_analysis(
            access_token=token,
            image_url=request.image_url,
            caption=result,
            description=request.description
        )
        
        return {
            "success": True,
            "caption": result,
            "image_url": request.image_url,
            "analysis_id": db_result.get("data", {}).get("id")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

@router.get("/autoglm/status")
async def autoglm_status():
    return autoglm_model_service.get_loading_status()