import open_clip
from PIL import Image
import torch

class CLIPModelService:
    def __init__(self):
        self.model_loaded = False
        self.loading_status = "Not started"
        self.loading_progress = 0
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        try:
            self.loading_status = "Loading model..."
            self.loading_progress = 30
            self.model, self.preprocess_train, self.preprocess_val = open_clip.create_model_and_transforms(
                'hf-hub:laion/CLIP-ViT-B-32-laion2B-s34B-b79K', device=self.device
            )
            self.loading_status = "Loading tokenizer..."
            self.loading_progress = 70
            self.tokenizer = open_clip.get_tokenizer('hf-hub:laion/CLIP-ViT-B-32-laion2B-s34B-b79K')
            self.loading_status = "Ready"
            self.loading_progress = 100
            self.model_loaded = True
        except Exception as e:
            self.loading_status = f"Error: {e}"
            self.loading_progress = 0
            self.model_loaded = False

    def get_loading_status(self):
        return {
            "loaded": self.model_loaded,
            "status": self.loading_status,
            "progress": self.loading_progress
        }

    def image_text_similarity(self, image: Image.Image, text: str) -> float:
        image_input = self.preprocess_val(image).unsqueeze(0).to(self.device)
        text_input = self.tokenizer([text]).to(self.device)
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text_input)
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features /= text_features.norm(dim=-1, keepdim=True)
            similarity = (image_features @ text_features.T).item()
        return similarity

clip_model_service = CLIPModelService()