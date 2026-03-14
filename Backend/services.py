import shutil
import os
import sys
from pathlib import Path
from fastapi import UploadFile

sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.embedding_manager import load_or_create_embeddings
    from similarity_engine import find_similar_images
    print("✅ Successfully loaded ML modules!")
except ImportError as e:
    print(f"⚠️ Could not load ML modules: {e}")

UPLOAD_DIR = Path("temp")
UPLOAD_DIR.mkdir(exist_ok=True)

try:
    embeddings = load_or_create_embeddings()
    print("✅ ML model loaded!")
except:
    embeddings = None
    print("❌ Failed to load ML model")


def get_verdict(score):
    if score >= 0.90:
        return "NOT SAFE"
    elif score >= 0.75:
        return "RISKY"
    elif score >= 0.55:
        return "MEDIUM"
    else:
        return "SAFE TO MINT"


async def validate_image(file: UploadFile):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if embeddings is None:
        return {
            "status": "error",
            "verdict": "UNKNOWN",
            "top_score": 0,
            "similar_images": [],
            "message": "ML model not loaded"
        }

    try:
        results = find_similar_images(str(file_path), embeddings)

        similar_images = []
        for r in results[:5]:
            similar_images.append({
                "filename": r.get("filename", "unknown"),
                "similarity_score": r.get("score", 0.0),
                "image_url": r.get("image_url", "")
            })

        top_score = similar_images[0]["similarity_score"] if similar_images else 0
        verdict = get_verdict(top_score)

        file_path.unlink()

        return {
            "status": "success",
            "verdict": verdict,
            "top_score": round(top_score * 100, 2),
            "similar_images": similar_images
        }

    except Exception as e:
        return {
            "status": "error",
            "verdict": "UNKNOWN",
            "top_score": 0,
            "similar_images": [],
            "message": str(e)
        }