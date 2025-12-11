"""
Pneumonia Detection API endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse
from services.supabase_service import supabase_service
from models.pneumonia_model import pneumonia_model_service
from PIL import Image
import io
from typing import Optional

router = APIRouter()


@router.get("/pneumonia/status")
async def get_pneumonia_status():
    """Get pneumonia model loading status"""
    status = pneumonia_model_service.get_loading_status()
    return {
        "success": True,
        "model": "Pneumonia Detection (Chest X-ray)",
        "status": status
    }


@router.post("/pneumonia/analyze")
async def analyze_xray(
    image: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Analyze chest X-ray image for pneumonia detection
    
    Requires:
    - image: Chest X-ray image file (JPEG, PNG)
    - Authorization header with Bearer token
    
    Returns:
    - Pneumonia detection results with confidence scores
    - Image stored in pneumonia_images bucket
    - Analysis saved to pneumonia_analyses table
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    print("\n" + "="*70)
    print("🩺 NEW PNEUMONIA DETECTION REQUEST")
    print("="*70)
    
    try:
        # Read and validate image
        print(f"📥 Image received: {image.filename} ({image.size} bytes)")
        
        image_data = await image.read()
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
        
        # Check model status
        status = pneumonia_model_service.get_loading_status()
        if not status["loaded"]:
            raise HTTPException(
                status_code=503,
                detail=f"Pneumonia model not ready: {status['status']} ({status['progress']}%)"
            )
        
        # Open image with PIL
        pil_image = Image.open(io.BytesIO(image_data))
        print(f"📐 Image opened: {pil_image.size} pixels, mode: {pil_image.mode}")
        
        # Upload to pneumonia_images bucket
        print("☁️  Uploading to pneumonia_images bucket...")
        upload_result = supabase_service.upload_pneumonia_image(
            access_token=token,
            image_data=image_data,
            filename=image.filename
        )
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to upload image: {upload_result.get('error')}"
            )
        
        image_url = upload_result["url"]
        print(f"✅ Image uploaded: {image_url}")
        
        # Classify X-ray
        print("🩺 Analyzing X-ray with pneumonia detection model...")
        classification_result = pneumonia_model_service.classify_xray(pil_image)
        
        print(f"✅ Classification complete:")
        print(f"   Prediction: {classification_result['prediction']}")
        print(f"   Confidence: {classification_result['confidence_percentage']}%")
        print(f"   Severity: {classification_result['severity']}")
        
        # Save to pneumonia_analyses table
        print("💾 Saving analysis to pneumonia_analyses table...")
        
        db_result = supabase_service.create_pneumonia_analysis(
            access_token=token,
            image_url=image_url,
            prediction=classification_result['prediction'],
            confidence=classification_result['confidence'],
            confidence_percentage=classification_result['confidence_percentage'],
            is_pneumonia=classification_result['is_pneumonia'],
            severity=classification_result['severity'],
            recommendation=classification_result['recommendation'],
            all_predictions=classification_result['all_predictions'],
            processing_time=classification_result['processing_time'],
            model_name=classification_result['model']
        )
        
        if not db_result["success"]:
            print(f"⚠️  Warning: Failed to save to database: {db_result.get('error')}")
        else:
            print(f"✅ Analysis saved to database (ID: {db_result['data']['id']})")
        
        print("="*70)
        print("✅ PNEUMONIA DETECTION COMPLETE")
        print("="*70 + "\n")
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Chest X-ray analyzed successfully",
                "data": {
                    "image_url": image_url,
                    "classification": classification_result,
                    "analysis_id": db_result['data']['id'] if db_result["success"] else None,
                    "created_at": db_result['data'].get('created_at') if db_result["success"] else None
                }
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error analyzing X-ray: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze X-ray: {str(e)}"
        )


@router.get("/pneumonia/history")
async def get_pneumonia_history(authorization: Optional[str] = Header(None)):
    """Get all pneumonia detection analyses for the authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.get_pneumonia_analyses(token)
    
    if result["success"]:
        return {
            "success": True,
            "data": result["data"],
            "count": result["count"]
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to fetch analyses")
        )


@router.get("/pneumonia/analyze/{analysis_id}")
async def get_pneumonia_analysis(
    analysis_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get a specific pneumonia analysis"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.get_pneumonia_analysis(token, analysis_id)
    
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


@router.delete("/pneumonia/analyze/{analysis_id}")
async def delete_pneumonia_analysis(
    analysis_id: int,
    authorization: Optional[str] = Header(None)
):
    """Delete a pneumonia analysis"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.delete_pneumonia_analysis(token, analysis_id)
    
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