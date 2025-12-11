"""
Vision AI API endpoints - Separate from health records
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File
from services.supabase_service import supabase_service
from models.vision_model import vision_model_service
from typing import Optional
from PIL import Image
import io
import time

router = APIRouter()


@router.post("/vision/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """Analyze an image with Vision AI and store in database"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        print("\n" + "="*70)
        print("🖼️  NEW VISION ANALYSIS REQUEST")
        print("="*70)
        
        # Read image data
        image_data = await image.read()
        print(f"📥 Image received: {image.filename} ({len(image_data)} bytes)")
        
        # Upload to Supabase storage
        print("☁️  Uploading to Supabase storage...")
        upload_start = time.time()
        upload_result = supabase_service.upload_image(
            access_token=token,
            image_data=image_data,
            filename=image.filename
        )
        upload_time = time.time() - upload_start
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to upload image: {upload_result.get('error')}"
            )
        
        image_url = upload_result["url"]
        print(f"✅ Image uploaded in {upload_time:.2f}s")
        print(f"🔗 URL: {image_url}")
        
        # Check if vision model is loaded
        if not vision_model_service.model_loaded:
            print("⚠️  Vision model not loaded, attempting to load...")
            loaded = vision_model_service.load_model()
            if not loaded:
                raise HTTPException(
                    status_code=503,
                    detail="Vision model not available. Please try again later."
                )
        
        # Generate AI description
        print("🤖 Generating AI description...")
        pil_image = Image.open(io.BytesIO(image_data))
        ai_start = time.time()
        ai_result = vision_model_service.generate_description(pil_image)
        ai_time = time.time() - ai_start
        
        ai_description = ai_result["generated_text"]
        processing_time = ai_result["processing_time"]
        model_name = ai_result["model"]
        
        print(f"✅ AI analysis completed in {ai_time:.2f}s")
        print(f"📝 Description: {ai_description[:100]}...")
        
        # Store analysis in database
        print("💾 Storing analysis in database...")
        db_start = time.time()
        result = supabase_service.create_vision_analysis(
            access_token=token,
            image_url=image_url,
            ai_description=ai_description,
            processing_time=processing_time,
            model_name=model_name
        )
        db_time = time.time() - db_start
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to store analysis")
            )
        
        print(f"✅ Analysis stored in {db_time:.2f}s")
        
        total_time = time.time() - upload_start
        print("="*70)
        print(f"✨ ANALYSIS COMPLETE - Total time: {total_time:.2f}s")
        print("="*70 + "\n")
        
        return {
            "success": True,
            "message": "Image analyzed successfully",
            "data": result["data"]
        }
        
    except Exception as e:
        print(f"❌ Error analyzing image: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze image: {str(e)}"
        )


@router.get("/vision/history")
async def get_analysis_history(authorization: Optional[str] = Header(None)):
    """Get all vision analyses for the authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.get_vision_analyses(token)
    
    if result["success"]:
        return {
            "success": True,
            "data": result["data"],
            "count": result["count"]
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to fetch history")
        )


@router.get("/vision/analyze/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get a specific vision analysis"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.get_vision_analysis(token, analysis_id)
    
    if result["success"]:
        return {
            "success": True,
            "data": result["data"]
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Analysis not found")
        )


@router.delete("/vision/analyze/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    authorization: Optional[str] = Header(None)
):
    """Delete a vision analysis"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.delete_vision_analysis(token, analysis_id)
    
    if result["success"]:
        return {
            "success": True,
            "message": result["message"]
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to delete analysis")
        )


@router.get("/vision/status")
async def get_vision_status():
    """Get vision model loading status"""
    status = vision_model_service.get_loading_status()
    return {
        "success": True,
        "model_loaded": status["loaded"],
        "status": status["status"],
        "progress": status["progress"],
        "model_name": vision_model_service.model_name if status["loaded"] else None
    }