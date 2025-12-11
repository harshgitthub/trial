"""
Vision Model Service - Image to Text Generation using BLIP
"""
from transformers import pipeline
from PIL import Image
from typing import Dict
import time
import torch


class VisionModelService:
    """Service for BLIP vision-to-text model"""
    
    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.model_name = "Salesforce/blip-image-captioning-large"
        self.loading_status = "Not started"
        self.loading_progress = 0
        
        # Auto-load model on initialization
        print("\n" + "="*70)
        print("🚀 AUTO-LOADING VISION MODEL ON STARTUP")
        print("="*70)
        self.load_model()
    
    def load_model(self) -> bool:
        """Load the vision model using pipeline"""
        if self.model_loaded:
            print("   ✓ Vision model already loaded")
            return True
        
        try:
            print("=" * 60)
            print(f"🔄 Loading Vision model: {self.model_name}")
            print("   Using BLIP (Bootstrap Language-Image Pre-training)")
            print("   This may take 2-5 minutes on first load...")
            print("   Model size: ~1-2 GB (will be cached for future use)")
            print("=" * 60)
            
            self.loading_status = "Loading pipeline..."
            self.loading_progress = 20
            print(f"\n📥 Loading image-to-text pipeline...")
            print("   ⏳ Downloading model and processor...")
            
            start_time = time.time()
            
            # Determine device
            device = 0 if torch.cuda.is_available() else -1
            device_name = "cuda" if device == 0 else "cpu"
            
            print(f"   📍 Target device: {device_name}")
            if device == 0:
                print(f"   🎮 GPU detected: {torch.cuda.get_device_name(0)}")
                print(f"   💾 GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            else:
                print(f"   💻 Running on CPU (slower but works)")
            
            self.loading_progress = 50
            
            # Load pipeline with BLIP model
            self.pipe = pipeline(
                "image-to-text",
                model=self.model_name,
                device=device
            )
            
            load_time = time.time() - start_time
            
            self.loading_progress = 100
            self.loading_status = "Ready"
            self.model_loaded = True
            
            print("\n" + "=" * 60)
            print("✅ Vision model loaded successfully!")
            print(f"   📊 Total loading time: {load_time:.2f}s ({load_time/60:.2f} minutes)")
            print(f"   📍 Running on: {device_name}")
            print(f"   🎯 Status: Ready to generate descriptions")
            print(f"   🏷️  Model: BLIP Image Captioning")
            print("=" * 60 + "\n")
            
            return True
            
        except Exception as e:
            self.loading_status = f"Error: {str(e)}"
            self.loading_progress = 0
            print("\n" + "=" * 60)
            print(f"❌ Error loading vision model: {e}")
            print("=" * 60)
            import traceback
            traceback.print_exc()
            self.model_loaded = False
            return False
    
    def get_loading_status(self) -> Dict:
        """Get current loading status"""
        return {
            "loaded": self.model_loaded,
            "status": self.loading_status,
            "progress": self.loading_progress
        }
    
    def generate_description(self, image: Image.Image, prompt: str = None) -> Dict:
        """
        Generate text description from an image
        
        Args:
            image: PIL Image
            prompt: Optional text prompt (BLIP supports conditional generation)
            
        Returns:
            Dict with generated text and metadata
        """
        if not self.model_loaded:
            raise Exception(f"Vision model not loaded. Status: {self.loading_status} ({self.loading_progress}%)")
        
        start_time = time.time()
        
        try:
            # Ensure RGB
            if image.mode != 'RGB':
                print(f"   🔄 Converting image from {image.mode} to RGB")
                image = image.convert('RGB')
            
            print(f"   📐 Image size: {image.size}")
            
            # Generate description using pipeline
            print("   🤖 Generating description...")
            generation_start = time.time()
            
            # BLIP can use conditional generation with text prompt
            if prompt:
                print(f"   📝 Using prompt: {prompt}")
                results = self.pipe(image, text=prompt, max_new_tokens=100)
            else:
                print("   📝 Generating unconditional caption")
                results = self.pipe(image, max_new_tokens=100)
            
            generation_time = time.time() - generation_start
            print(f"   ⚡ Generation took {generation_time:.2f}s")
            
            # Extract generated text from results
            if isinstance(results, list) and len(results) > 0:
                generated_text = results[0].get('generated_text', '')
            else:
                generated_text = str(results)
            
            processing_time = time.time() - start_time
            
            print(f"   ✅ Total processing time: {processing_time:.2f}s")
            print(f"   📝 Generated text ({len(generated_text)} chars): {generated_text[:100]}...")
            
            return {
                "generated_text": generated_text,
                "prompt": prompt,
                "processing_time": round(processing_time, 2),
                "model": self.model_name
            }
            
        except Exception as e:
            print(f"   ❌ Error generating description: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to generate description: {str(e)}")


# Singleton instance - model loads immediately when imported
vision_model_service = VisionModelService()