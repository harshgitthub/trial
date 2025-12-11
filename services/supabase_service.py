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
    STORAGE_BUCKET = "health-images"  # Changed from storage_1
    
    def __init__(self):
        print("\n" + "="*60)
        print("🔧 INITIALIZING SUPABASE SERVICE")
        print("="*60)
        
        # Regular client (anon key) - for auth
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
        print("✅ Regular client created (anon key)")
        
        # Admin client (service role key) - for storage/database
        print(f"\n🔑 Checking service role key...")
        print(f"   URL: {settings.supabase_url}")
        print(f"   Key length: {len(settings.supabase_service_role_key)} chars")
        
        if len(settings.supabase_service_role_key) < 100:
            print("❌ WARNING: Service role key seems too short!")
            print("   Expected: 400-600 characters")
        
        try:
            self.admin_supabase: Client = create_client(
                settings.supabase_url,
                settings.supabase_service_role_key
            )
            print("✅ Admin client created (service role key)")
            
            # Test the admin client
            buckets = self.admin_supabase.storage.list_buckets()
            print(f"\n📦 Found {len(buckets)} storage buckets:")
            for bucket in buckets:
                print(f"   • {bucket.name} (public: {bucket.public})")
            
            # Verify our bucket exists
            if self.STORAGE_BUCKET in [b.name for b in buckets]:
                print(f"✅ Target bucket '{self.STORAGE_BUCKET}' found!")
            else:
                print(f"⚠️  WARNING: Bucket '{self.STORAGE_BUCKET}' not found!")
                
            print("\n✅ Admin client is working!")
            
        except Exception as e:
            print(f"\n❌ ADMIN CLIENT FAILED: {e}")
            print("⚠️  Check your SUPABASE_SERVICE_ROLE_KEY in .env")
        
        print("="*60 + "\n")

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
            
            # Generate unique filename with user ID as folder
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{user['id']}/{uuid.uuid4()}.{file_extension}"
            
            print(f"📤 Uploading to: {self.STORAGE_BUCKET}/{unique_filename}")
            print(f"📦 File size: {len(image_data)} bytes")
            
            # Upload using admin client with service role
            self.admin_supabase.storage.from_(self.STORAGE_BUCKET).upload(
                path=unique_filename,
                file=image_data,
                file_options={
                    "content-type": f"image/{file_extension}",
                    "cache-control": "3600",
                    "upsert": "true"
                }
            )
            
            # Get public URL
            public_url = self.admin_supabase.storage.from_(self.STORAGE_BUCKET).get_public_url(unique_filename)
            
            print(f"✅ Upload successful!")
            print(f"🔗 Public URL: {public_url}")
            
            return {
                "success": True,
                "url": public_url,
                "path": unique_filename
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Upload failed: {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": error_msg
            }
    
    # Health Records Methods
    def create_health_record(self, access_token: str, title: str, description: str, 
                           category: str, date: str) -> Dict:
        """Create a new health record"""
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
        
    def upload_mnist_image(self, access_token: str, image_data: bytes, filename: str) -> dict:
        """Upload MNIST image to Supabase storage"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            import uuid
            file_ext = filename.split('.')[-1] if '.' in filename else 'png'
            unique_filename = f"{user['id']}/{uuid.uuid4()}.{file_ext}"
            self.admin_supabase.storage.from_("mnist_images").upload(
                path=unique_filename,
                file=image_data,
                file_options={
                    "content-type": f"image/{file_ext}",
                    "cache-control": "3600",
                    "upsert": "true"
                }
            )
            public_url = self.admin_supabase.storage.from_("mnist_images").get_public_url(unique_filename)
            return {"success": True, "url": public_url, "path": unique_filename}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_autoglm_analysis(self, access_token: str, image_url: str, caption: str, description: str = None) -> dict:
        """Save BLIP image caption result to Supabase table"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            data = {
                "user_id": user["id"],
                "image_url": image_url,
                "caption": caption,
                "description": description,
            }
            response = self.admin_supabase.table("autoglm_analyses").insert(data).execute()
            return {"success": True, "data": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    def create_mnist_analysis(self, access_token: str, image_url: str, prediction: int, probabilities: list, filename: str) -> dict:
        """Save MNIST inference result to Supabase table"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            data = {
                "user_id": user["id"],
                "image_url": image_url,
                "prediction": prediction,
                "probabilities": probabilities,
                "filename": filename,
            }
            response = self.admin_supabase.table("mnist_analyses").insert(data).execute()
            return {"success": True, "data": response.data[0] if response.data else None}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
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
    
    # Pneumonia Analysis Methods
    def upload_pneumonia_image(self, access_token: str, image_data: bytes, filename: str) -> Dict:
        """Upload pneumonia X-ray image to Supabase storage"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            # Generate unique filename with user ID as folder
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            unique_filename = f"{user['id']}/{uuid.uuid4()}.{file_extension}"
            
            print(f"📤 Uploading pneumonia X-ray to: pneumonia_images/{unique_filename}")
            print(f"📦 File size: {len(image_data)} bytes")
            
            # Upload using admin client with service role
            self.admin_supabase.storage.from_("pneumonia_images").upload(
                path=unique_filename,
                file=image_data,
                file_options={
                    "content-type": f"image/{file_extension}",
                    "cache-control": "3600",
                    "upsert": "true"
                }
            )
            
            # Get public URL
            public_url = self.admin_supabase.storage.from_("pneumonia_images").get_public_url(unique_filename)
            
            print(f"✅ Pneumonia X-ray uploaded!")
            print(f"🔗 Public URL: {public_url}")
            
            return {
                "success": True,
                "url": public_url,
                "path": unique_filename
            }
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Upload failed: {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def create_pneumonia_analysis(self, access_token: str, image_url: str,
                                  prediction: str, confidence: float,
                                  confidence_percentage: float, is_pneumonia: bool,
                                  severity: str, recommendation: str,
                                  all_predictions: list, processing_time: float,
                                  model_name: str) -> Dict:
        """Create a new pneumonia analysis record"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            data = {
                "user_id": user["id"],
                "image_url": image_url,
                "prediction": prediction,
                "confidence": confidence,
                "confidence_percentage": confidence_percentage,
                "is_pneumonia": is_pneumonia,
                "severity": severity,
                "recommendation": recommendation,
                "all_predictions": all_predictions,
                "processing_time": processing_time,
                "model_name": model_name
            }
            
            print(f"📝 Creating pneumonia analysis record...")
            print(f"   Prediction: {prediction}")
            print(f"   Confidence: {confidence_percentage}%")
            
            response = self.admin_supabase.table("pneumonia_analyses").insert(data).execute()
            
            print(f"✅ Pneumonia analysis saved (ID: {response.data[0]['id']})")
            
            return {
                "success": True,
                "data": response.data[0] if response.data else None,
                "message": "Pneumonia analysis created successfully"
            }
            
        except Exception as e:
            print(f"❌ Error creating pneumonia analysis: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pneumonia_analyses(self, access_token: str) -> Dict:
        """Get all pneumonia analyses for a user"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("pneumonia_analyses")\
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
            print(f"❌ Error fetching pneumonia analyses: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_pneumonia_analysis(self, access_token: str, analysis_id: int) -> Dict:
        """Get a specific pneumonia analysis"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("pneumonia_analyses")\
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
    
    def create_clip_analysis(self, access_token: str, image_url: str, text: str, similarity_score: float, filename: str) -> Dict:
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            data = {
                "user_id": user["id"],
                "image_url": image_url,
                "text": text,
                "similarity_score": similarity_score,
                "filename": filename,
            }
            response = self.admin_supabase.table("clip_analyses").insert(data).execute()
            return {
                "success": True,
                "data": response.data[0] if response.data else None,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        
    def delete_pneumonia_analysis(self, access_token: str, analysis_id: int) -> Dict:
        """Delete a pneumonia analysis"""
        try:
            user = self.get_user(access_token)
            if not user:
                return {"success": False, "error": "Invalid token"}
            
            response = self.admin_supabase.table("pneumonia_analyses")\
                .delete()\
                .eq("id", analysis_id)\
                .eq("user_id", user["id"])\
                .execute()
            
            return {
                "success": True,
                "message": "Pneumonia analysis deleted successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# Singleton instance
supabase_service = SupabaseService()