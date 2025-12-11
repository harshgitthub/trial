from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from models.clip_model import clip_model_service
from services.supabase_service import supabase_service
from PIL import Image
import io
from typing import Optional

router = APIRouter()

@router.get("/clip/status")
async def clip_model_status():
    """
    Returns CLIP model loading status and progress.
    """
    return clip_model_service.get_loading_status()

@router.post("/clip/similarity")
async def clip_similarity(
    image: UploadFile = File(...),
    text: str = "",
    authorization: Optional[str] = Header(None)
):
    """
    Returns CLIP similarity score between uploaded image and input text.
    Also saves result to Supabase (table: clip_analyses).
    """
    try:
        # Auth
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        token = authorization.replace("Bearer ", "")

        # Read image
        image_data = await image.read()
        pil_image = Image.open(io.BytesIO(image_data)).convert("RGB")
        score = clip_model_service.image_text_similarity(pil_image, text)

        # Upload image to Supabase storage (bucket: clip_images)
        upload_result = supabase_service.upload_image(
            access_token=token,
            image_data=image_data,
            filename=image.filename
        )
        if not upload_result["success"]:
            raise HTTPException(status_code=400, detail=f"Image upload failed: {upload_result['error']}")
        image_url = upload_result["url"]

        # Save analysis to Supabase (table: clip_analyses)
        db_result = supabase_service.create_clip_analysis(
            access_token=token,
            image_url=image_url,
            text=text,
            similarity_score=score,
            filename=image.filename
        )

        return {
            "success": True,
            "similarity_score": score,
            "text": text,
            "filename": image.filename,
            "image_url": image_url,
            "analysis_id": db_result.get("data", {}).get("id")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CLIP similarity failed: {str(e)}")