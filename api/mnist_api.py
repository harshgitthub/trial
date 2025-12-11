from fastapi import APIRouter, UploadFile, File, HTTPException, Header
from PIL import Image
import torch
import numpy as np
import io
from typing import Optional
from services.supabase_service import supabase_service

router = APIRouter()

MODEL_PATH = "models/mnist_cnn_mobile.pt"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = torch.jit.load(MODEL_PATH, map_location=DEVICE)
model.eval()

@router.post("/mnist/infer")
async def mnist_infer(
    image: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
):
    """
    Predict MNIST digit from uploaded 28x28 grayscale image.
    Stores input and output in Supabase.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    token = authorization.replace("Bearer ", "")

    try:
        # Read and preprocess image
        image_bytes = await image.read()
        pil_img = Image.open(io.BytesIO(image_bytes)).convert("L").resize((28, 28))
        img_np = np.array(pil_img).astype(np.float32) / 255.0
        img_tensor = torch.tensor(img_np).unsqueeze(0).unsqueeze(0).to(DEVICE)

        # Inference
        with torch.no_grad():
            logits = model(img_tensor)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
            pred = int(np.argmax(probs))

        # Upload image to Supabase
        upload_result = supabase_service.upload_mnist_image(
            access_token=token,
            image_data=image_bytes,
            filename=image.filename
        )
        if not upload_result["success"]:
            raise HTTPException(status_code=400, detail=f"Image upload failed: {upload_result['error']}")
        image_url = upload_result["url"]

        # Save analysis to Supabase
        db_result = supabase_service.create_mnist_analysis(
            access_token=token,
            image_url=image_url,
            prediction=pred,
            probabilities=[float(p) for p in probs],
            filename=image.filename
        )

        return {
            "success": True,
            "prediction": pred,
            "probabilities": [float(p) for p in probs],
            "image_url": image_url,
            "analysis_id": db_result.get("data", {}).get("id")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")