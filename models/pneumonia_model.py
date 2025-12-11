"""
Pneumonia Detection Model Service - Chest X-ray Classification
"""
from transformers import pipeline
from PIL import Image
from typing import Dict
import time
import torch


class PneumoniaModelService:
    """Service for Pneumonia Detection using ViT fine-tuned on Chest X-rays"""
    
    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.model_name = "nickmuchi/vit-finetuned-chest-xray-pneumonia"
        self.loading_status = "Not started"
        self.loading_progress = 0
        
        # Auto-load model on initialization
        print("\n" + "="*70)
        print("🩺 AUTO-LOADING PNEUMONIA DETECTION MODEL ON STARTUP")
        print("="*70)
        self.load_model()
    
    def load_model(self) -> bool:
        """Load the pneumonia detection model using pipeline"""
        if self.model_loaded:
            print("   ✓ Pneumonia model already loaded")
            return True
        
        try:
            print("=" * 60)
            print(f"🔄 Loading Pneumonia Detection model: {self.model_name}")
            print("   Using ViT (Vision Transformer) fine-tuned on Chest X-rays")
            print("   This may take 2-3 minutes on first load...")
            print("   Model size: ~300-500 MB (will be cached for future use)")
            print("=" * 60)

            self.loading_status = "Loading pipeline..."
            self.loading_progress = 20
            print(f"\n📥 Loading image classification pipeline...")
            print("   ⏳ Downloading model and processor...")
            
            start_time = time.time()
            
            device = 0 if torch.cuda.is_available() else -1
            device_name = "cuda" if device == 0 else "cpu"
            
            print(f"   📍 Target device: {device_name}")
            if device == 0:
                print(f"   🎮 GPU detected: {torch.cuda.get_device_name(0)}")
                print(f"   💾 GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            else:
                print(f"   💻 Running on CPU (slower but works)")
            
            self.loading_progress = 50
            
            # Load pipeline with fine-tuned ViT model
            self.pipe = pipeline(
                "image-classification",
                model=self.model_name,
                device=device
            )
            
            load_time = time.time() - start_time
            
            self.loading_progress = 100
            self.loading_status = "Ready"
            self.model_loaded = True
            
            print("\n" + "=" * 60)
            print("✅ Pneumonia Detection model loaded successfully!")
            print(f"   📊 Total loading time: {load_time:.2f}s ({load_time/60:.2f} minutes)")
            print(f"   📍 Running on: {device_name}")
            print(f"   🎯 Status: Ready to classify chest X-rays")
            print(f"   🏷️  Model: ViT fine-tuned on Chest X-ray dataset")
            print(f"   🏥 Classes: NORMAL, PNEUMONIA")
            print("=" * 60 + "\n")
            
            return True
            
        except Exception as e:
            self.loading_status = f"Error: {str(e)}"
            self.loading_progress = 0
            print("\n" + "=" * 60)
            print(f"❌ Error loading pneumonia model: {e}")
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
            "progress": self.loading_progress,
            "model_name": self.model_name
        }
    
    def classify_xray(self, image: Image.Image) -> Dict:
        """
        Classify chest X-ray image for pneumonia detection
        
        Args:
            image: PIL Image of chest X-ray
            
        Returns:
            Dict with classification results and confidence scores
        """
        if not self.model_loaded:
            raise Exception(f"Pneumonia model not loaded. Status: {self.loading_status} ({self.loading_progress}%)")
        
        start_time = time.time()
        
        try:
            # Ensure RGB
            if image.mode != 'RGB':
                print(f"   🔄 Converting image from {image.mode} to RGB")
                image = image.convert('RGB')
            
            print(f"   📐 Image size: {image.size}")
            
            # Classify using pipeline
            print("   🩺 Analyzing chest X-ray...")
            classification_start = time.time()
            
            results = self.pipe(image)
            
            classification_time = time.time() - classification_start
            print(f"   ⚡ Classification took {classification_time:.2f}s")
            
            # Process results
            # results is a list like:
            # [{'label': 'PNEUMONIA', 'score': 0.95}, {'label': 'NORMAL', 'score': 0.05}]
            
            if not results or len(results) == 0:
                raise Exception("No classification results returned")
            
            # Get top prediction
            top_prediction = results[0]
            prediction_label = top_prediction['label']
            confidence = top_prediction['score']
            
            # Get all predictions sorted by confidence
            all_predictions = sorted(results, key=lambda x: x['score'], reverse=True)
            
            processing_time = time.time() - start_time
            
            # Determine severity and recommendation
            is_pneumonia = prediction_label.upper() == 'PNEUMONIA'
            severity = self._determine_severity(confidence, is_pneumonia)
            recommendation = self._get_recommendation(is_pneumonia, confidence)
            
            print(f"   ✅ Total processing time: {processing_time:.2f}s")
            print(f"   🏷️  Prediction: {prediction_label} ({confidence*100:.2f}% confidence)")
            print(f"   ⚠️  Severity: {severity}")
            
            return {
                "prediction": prediction_label,
                "confidence": round(confidence, 4),
                "confidence_percentage": round(confidence * 100, 2),
                "is_pneumonia": is_pneumonia,
                "severity": severity,
                "recommendation": recommendation,
                "all_predictions": [
                    {
                        "label": pred['label'],
                        "confidence": round(pred['score'], 4),
                        "percentage": round(pred['score'] * 100, 2)
                    }
                    for pred in all_predictions
                ],
                "processing_time": round(processing_time, 2),
                "model": self.model_name
            }
            
        except Exception as e:
            print(f"   ❌ Error classifying X-ray: {e}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to classify X-ray: {str(e)}")
    
    def _determine_severity(self, confidence: float, is_pneumonia: bool) -> str:
        """Determine severity level based on prediction confidence"""
        if not is_pneumonia:
            return "Normal"
        
        if confidence >= 0.95:
            return "High Confidence - Pneumonia Detected"
        elif confidence >= 0.80:
            return "Moderate Confidence - Pneumonia Likely"
        elif confidence >= 0.60:
            return "Low Confidence - Pneumonia Possible"
        else:
            return "Very Low Confidence - Unclear"
    
    def _get_recommendation(self, is_pneumonia: bool, confidence: float) -> str:
        """Get medical recommendation based on prediction"""
        if not is_pneumonia:
            if confidence >= 0.90:
                return "X-ray appears normal. Continue regular health monitoring."
            else:
                return "X-ray appears mostly normal, but confidence is moderate. Consider follow-up if symptoms persist."
        
        if confidence >= 0.90:
            return "⚠️ HIGH PRIORITY: Pneumonia detected with high confidence. Immediate medical consultation strongly recommended."
        elif confidence >= 0.75:
            return "⚠️ MODERATE PRIORITY: Pneumonia likely detected. Please consult a healthcare provider soon for proper diagnosis."
        elif confidence >= 0.60:
            return "⚠️ LOW PRIORITY: Possible pneumonia indication. Monitor symptoms and consider medical consultation if condition worsens."
        else:
            return "Results inconclusive. If experiencing respiratory symptoms, please consult a healthcare provider."


# Singleton instance - model loads immediately when imported
pneumonia_model_service = PneumoniaModelService()