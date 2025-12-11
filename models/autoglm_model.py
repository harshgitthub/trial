from transformers import pipeline

class AutoGLMModelService:
    def __init__(self):
        # Using BLIP instead of unsupported GLM model
        self.model_name = "Salesforce/blip-image-captioning-base"
        self.pipe = pipeline("image-to-text", model=self.model_name)
        self.model_loaded = True
        print(f"✅ Model loaded: {self.model_name}")

    def infer(self, image_url: str):
        """Generate caption from image URL"""
        result = self.pipe(image_url)
        return result[0]['generated_text'] if result else None

    def get_loading_status(self):
        return {
            "loaded": self.model_loaded,
            "model_name": self.model_name
        }

autoglm_model_service = AutoGLMModelService()