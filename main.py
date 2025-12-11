"""
Newjilo Backend - FastAPI with Supabase Authentication and Vision AI
"""
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api.auth import router as auth_router
from api.records import router as records_router
from api.vision import router as vision_router
from api.pneumonia import router as pneumonia_router
from models.vision_model import vision_model_service
from models.pneumonia_model import pneumonia_model_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("\n" + "=" * 70)
    print("🚀 NEWJILO BACKEND STARTING")
    print("=" * 70)
    
    # Check vision model status
    vision_status = vision_model_service.get_loading_status()
    if vision_status["loaded"]:
        print("\n✅ Vision AI Model: READY")
    else:
        print(f"\n⚠️  Vision AI Model: {vision_status['status']}")
    
    # Check pneumonia model status
    pneumonia_status = pneumonia_model_service.get_loading_status()
    if pneumonia_status["loaded"]:
        print("✅ Pneumonia Detection Model: READY")
    else:
        print(f"⚠️  Pneumonia Detection Model: {pneumonia_status['status']}")
    
    print("\n" + "=" * 70)
    print("✅ NEWJILO BACKEND STARTED SUCCESSFULLY!")
    print("=" * 70)
    print("📋 Available Services:")
    print("   🔐 Authentication - /api/auth")
    print("   📝 Health Records - /api/records")
    print("   👁️  Vision AI - /api/vision")
    print("   🩺 Pneumonia Detection - /api/pneumonia")
    print("=" * 70)
    print("\n🎯 Backend is ready to receive requests!")
    print("=" * 70 + "\n")
    
    yield
    
    print("\n👋 Shutting down Newjilo Backend...")


app = FastAPI(
    title="Newjilo API",
    description="Authentication, Health Records, Vision AI, and Pneumonia Detection API with Supabase",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(records_router, prefix="/api", tags=["health-records"])
app.include_router(vision_router, prefix="/api", tags=["vision-ai"])
app.include_router(pneumonia_router, prefix="/api", tags=["pneumonia-detection"])


@app.get("/")
async def root():
    """Root endpoint"""
    vision_status = vision_model_service.get_loading_status()
    pneumonia_status = pneumonia_model_service.get_loading_status()
    
    return {
        "message": "Newjilo API with Vision AI and Pneumonia Detection",
        "version": "1.0.0",
        "models": {
            "vision_ai": {
                "loaded": vision_status["loaded"],
                "status": vision_status["status"]
            },
            "pneumonia_detection": {
                "loaded": pneumonia_status["loaded"],
                "status": pneumonia_status["status"]
            }
        },
        "endpoints": {
            "auth": {
                "signup": "/api/auth/signup",
                "login": "/api/auth/login",
                "logout": "/api/auth/logout",
                "user": "/api/auth/user"
            },
            "records": {
                "create": "POST /api/records",
                "list": "GET /api/records",
                "get": "GET /api/records/{id}",
                "update": "PUT /api/records/{id}",
                "delete": "DELETE /api/records/{id}"
            },
            "vision": {
                "analyze": "POST /api/vision/analyze",
                "history": "GET /api/vision/history",
                "status": "GET /api/vision/status"
            },
            "pneumonia": {
                "analyze": "POST /api/pneumonia/analyze",
                "history": "GET /api/pneumonia/history",
                "status": "GET /api/pneumonia/status"
            }
        }
    }


from api.autoglm_api import router as autoglm_router

# ...existing code...

app.include_router(autoglm_router, prefix="/api", tags=["autoglm"])

from api.clip_api import router as clip_router

from api.mnist_api import router as mnist_router
app.include_router(mnist_router, prefix="/api", tags=["mnist"])

app.include_router(clip_router, prefix="/api", tags=["clip"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    vision_status = vision_model_service.get_loading_status()
    pneumonia_status = pneumonia_model_service.get_loading_status()
    
    return {
        "status": "healthy",
        "models": {
            "vision_ai": vision_status,
            "pneumonia_detection": pneumonia_status
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Newjilo Backend...")
    print("📍 Server will run on http://localhost:8000")
    print("📚 API docs will be at http://localhost:8000/docs")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )