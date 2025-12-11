"""
Configuration settings for Supabase
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""
    supabase_url: str
    supabase_key: str
    supabase_service_role_key: str
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    """Get cached settings"""
    return Settings()
"""
Supabase service for authentication and storage
"""
from supabase import create_client, Client
from config.settings import get_settings
from typing import Dict, Optional, List
from datetime import datetime
import io
import uuid

settings = get_settings()


class SupabaseService:
    """Service for Supabase operations"""
    
    # Storage bucket name
    STORAGE_BUCKET = "storage_1"  # Add this constant
    
    def __init__(self):
        # Client for authentication (uses anon key)
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        
        # Admin client for database operations (uses service role key)
        self.admin_supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_role_key
        )
    
    def sign_up(self, email: str, password: str, full_name: str) -> Dict:
        """Sign up a new user"""
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            if response.user:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "full_name": full_name
                    },
                    "session": {
                        "access_token": response.session.access_token if response.session else None,
                        "refresh_token": response.session.refresh_token if response.session else None
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create user"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_in(self, email: str, password: str) -> Dict:
        """Sign in an existing user"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                return {
                    "success": True,
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "full_name": response.user.user_metadata.get("full_name", "")
                    },
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid credentials"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def sign_out(self, access_token: str) -> Dict:
        """Sign out user"""
        try:
            self.supabase.auth.sign_out()
            return {
                "success": True,
                "message": "Signed out successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_user(self, access_token: str) -> Optional[Dict]:
        """Get user details from access token"""
        try:
            response = self.supabase.auth.get_user(access_token)
            if response.user:
                return {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": response.user.user_metadata.get("full_name", "")
                }
            return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    # Image Storage Methods
    def upload_image(self, access_token: str, image_data: bytes, filename: str) -> Dict:
        """Upload image to Supabase storage"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            # Generate unique filename
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{user['id']}/{uuid.uuid4()}.{file_extension}"
            
            print(f"📤 Uploading image to bucket: {self.STORAGE_BUCKET}")
            print(f"📂 Path: {unique_filename}")
            
            # Upload to Supabase storage using admin client
            response = self.admin_supabase.storage.from_(self.STORAGE_BUCKET).upload(
                path=unique_filename,
                file=image_data,
                file_options={
                    "content-type": f"image/{file_extension}",
                    "upsert": "false"
                }
            )
            
            # Get public URL
            public_url = self.admin_supabase.storage.from_(self.STORAGE_BUCKET).get_public_url(unique_filename)
            
            print(f"✅ Image uploaded successfully!")
            print(f"🔗 URL: {public_url}")
            
            return {
                "success": True,
                "url": public_url,
                "path": unique_filename
            }
            
        except Exception as e:
            print(f"❌ Error uploading image: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    # Health Records Methods
    def create_health_record(self, access_token: str, title: str, description: str, 
                           category: str, date: str) -> Dict:
        """Create a new health record with optional image and AI description"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            data = {
                "user_id": user["id"],
                "title": title,
                "description": description,
                "category": category,
                "date": date
            }
            
            print(f"📝 Creating record with data: {data}")
            
            response = self.admin_supabase.table("health_records").insert(data).execute()
            
            print(f"✅ Record created: {response.data}")
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None,
                "message": "Health record created successfully"
            }
            
        except Exception as e:
            print(f"❌ Error creating record: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_health_records(self, access_token: str) -> Dict:
        """Get all health records for a user"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("health_records")\
                .select("*")\
                .eq("user_id", user["id"])\
                .order("date", desc=True)\
                .execute()
            
            return {
                "success": True,
                "data": response.data,
                "count": len(response.data)
            }
            
        except Exception as e:
            print(f"❌ Error fetching records: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_health_record(self, access_token: str, record_id: int) -> Dict:
        """Get a specific health record"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("health_records")\
                .select("*")\
                .eq("id", record_id)\
                .eq("user_id", user["id"])\
                .single()\
                .execute()
            
            return {
                "success": True,
                "data": response.data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_health_record(self, access_token: str, record_id: int, 
                           title: str, description: str, category: str, date: str) -> Dict:
        """Update a health record"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            data = {
                "title": title,
                "description": description,
                "category": category,
                "date": date
            }
            
            response = self.admin_supabase.table("health_records")\
                .update(data)\
                .eq("id", record_id)\
                .eq("user_id", user["id"])\
                .execute()
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None,
                "message": "Health record updated successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_health_record(self, access_token: str, record_id: int) -> Dict:
        """Delete a health record"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("health_records")\
                .delete()\
                .eq("id", record_id)\
                .eq("user_id", user["id"])\
                .execute()
            
            return {
                "success": True,
                "message": "Health record deleted successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # Vision Analysis Methods
    def create_vision_analysis(self, access_token: str, image_url: str, 
                             ai_description: str, processing_time: float,
                             model_name: str) -> Dict:
        """Create a new vision analysis record"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            data = {
                "user_id": user["id"],
                "image_url": image_url,
                "ai_description": ai_description,
                "processing_time": processing_time,
                "model_name": model_name
            }
            
            print(f"📝 Creating vision analysis: {data}")
            
            response = self.admin_supabase.table("vision_analysis").insert(data).execute()
            
            print(f"✅ Vision analysis created: {response.data}")
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None,
                "message": "Vision analysis created successfully"
            }
            
        except Exception as e:
            print(f"❌ Error creating vision analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_vision_analyses(self, access_token: str) -> Dict:
        """Get all vision analyses for a user"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("vision_analysis")\
                .select("*")\
                .eq("user_id", user["id"])\
                .order("created_at", desc=True)\
                .execute()
            
            return {
                "success": True,
                "data": response.data,
                "count": len(response.data)
            }
            
        except Exception as e:
            print(f"❌ Error fetching vision analyses: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_vision_analysis(self, access_token: str, analysis_id: int) -> Dict:
        """Get a specific vision analysis"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("vision_analysis")\
                .select("*")\
                .eq("id", analysis_id)\
                .eq("user_id", user["id"])\
                .single()\
                .execute()
            
            return {
                "success": True,
                "data": response.data
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_vision_analysis(self, access_token: str, analysis_id: int) -> Dict:
        """Delete a vision analysis"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("vision_analysis")\
                .delete()\
                .eq("id", analysis_id)\
                .eq("user_id", user["id"])\
                .execute()
            
            return {
                "success": True,
                "message": "Vision analysis deleted successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
supabase_service = SupabaseService()