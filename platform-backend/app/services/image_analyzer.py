import base64
import io
import requests
from PIL import Image

CANDIDATE_LABELS = [
    "a clean airplane seat", "a dirty airplane seat",
    "a clean airplane cabin", "a dirty airplane cabin",
    "a clean tray table", "a dirty tray table",
    "a clean window", "a dirty window",
    "a clean floor", "a dirty floor",
]

HF_API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"


def analyze_image(image_bytes: bytes) -> dict | None:
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img.thumbnail((512, 512))
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        b64 = base64.b64encode(buffered.getvalue()).decode()

        response = requests.post(
            HF_API_URL,
            json={
                "inputs": b64,
                "parameters": {"candidate_labels": CANDIDATE_LABELS},
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
        if response.status_code != 200:
            return None

        data = response.json()
        scores = list(
            zip(data.get("labels", []), data.get("scores", []))
        )

        clean_score = (
            sum(s for lbl, s in scores if lbl.startswith("a clean")) / 5.0
        )
        dirty_score = (
            sum(s for lbl, s in scores if lbl.startswith("a dirty")) / 5.0
        )
        top = max(scores, key=lambda x: x[1])

        return {
            "label": "clean" if clean_score > dirty_score else "dirty",
            "confidence": round(max(clean_score, dirty_score), 4),
            "topLabel": top[0],
            "topScore": round(top[1], 4),
        }
    except Exception:
        return None
