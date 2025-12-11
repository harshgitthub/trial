"""
Health Records API endpoints
"""
from fastapi import APIRouter, HTTPException, Header
from services.supabase_service import supabase_service
from typing import Optional
from pydantic import BaseModel

router = APIRouter()


class HealthRecordCreate(BaseModel):
    """Health record creation model"""
    title: str
    description: str
    category: str
    date: str


class HealthRecordUpdate(BaseModel):
    """Health record update model"""
    title: str
    description: str
    category: str
    date: str


@router.post("/records")
async def create_record(
    record: HealthRecordCreate,
    authorization: Optional[str] = Header(None)
):
    """Create a new health record"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        result = supabase_service.create_health_record(
            access_token=token,
            title=record.title,
            description=record.description,
            category=record.category,
            date=record.date
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to create record")
            )
            
    except Exception as e:
        print(f"❌ Error creating record: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create record: {str(e)}"
        )


@router.get("/records")
async def get_records(authorization: Optional[str] = Header(None)):
    """Get all health records for the authenticated user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.get_health_records(token)
    
    if result["success"]:
        return {
            "success": True,
            "data": result["data"],
            "count": result["count"]
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to fetch records")
        )


@router.get("/records/{record_id}")
async def get_record(
    record_id: int,
    authorization: Optional[str] = Header(None)
):
    """Get a specific health record"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.get_health_record(token, record_id)
    
    if result["success"]:
        return {
            "success": True,
            "data": result["data"]
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=result.get("error", "Record not found")
        )


@router.put("/records/{record_id}")
async def update_record(
    record_id: int,
    record: HealthRecordUpdate,
    authorization: Optional[str] = Header(None)
):
    """Update a health record"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        result = supabase_service.update_health_record(
            access_token=token,
            record_id=record_id,
            title=record.title,
            description=record.description,
            category=record.category,
            date=record.date
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "data": result["data"]
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Failed to update record")
            )
            
    except Exception as e:
        print(f"❌ Error updating record: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update record: {str(e)}"
        )


@router.delete("/records/{record_id}")
async def delete_record(
    record_id: int,
    authorization: Optional[str] = Header(None)
):
    """Delete a health record"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.delete_health_record(token, record_id)
    
    if result["success"]:
        return {
            "success": True,
            "message": result["message"]
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to delete record")
        )