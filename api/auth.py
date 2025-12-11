"""
Authentication API endpoints
"""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, EmailStr
from services.supabase_service import supabase_service
from typing import Optional

router = APIRouter()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def signup(request: SignUpRequest):
    """Sign up a new user"""
    result = supabase_service.sign_up(
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )
    
    if result["success"]:
        return {
            "success": True,
            "message": "User created successfully",
            "data": result
        }
    else:
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Failed to create user")
        )


@router.post("/login")
async def login(request: SignInRequest):
    """Login user"""
    result = supabase_service.sign_in(
        email=request.email,
        password=request.password
    )
    
    if result["success"]:
        return {
            "success": True,
            "message": "Logged in successfully",
            "data": result
        }
    else:
        raise HTTPException(
            status_code=401,
            detail=result.get("error", "Invalid credentials")
        )


@router.post("/logout")
async def logout(authorization: Optional[str] = Header(None)):
    """Logout user"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    result = supabase_service.sign_out(token)
    
    if result["success"]:
        return {
            "success": True,
            "message": "Logged out successfully"
        }
    else:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to logout"))


@router.get("/user")
async def get_user(authorization: Optional[str] = Header(None)):
    """Get current user details"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    user = supabase_service.get_user(token)
    
    if user:
        return {
            "success": True,
            "data": user
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
