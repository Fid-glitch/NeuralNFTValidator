import shutil
import os
import sys
from pathlib import Path
from fastapi import UploadFile

# Add parent directory to path so we can import teammate's modules
sys.path.append(str(Path(__file__).parent.parent))

try:
    from utils.embedding_manager import load_or_create_embeddings
    from similarity_engine import find_similar_images
    print("✅ Successfully loaded ML modules!")
except ImportError as e:
    print(f"⚠️ Could not load ML modules: {e}")
    print("Make sure embedding_manager.py and similarity_engine.py exist")

# Create temp folder if it doesn't exist
UPLOAD_DIR = Path("temp")
UPLOAD_DIR.mkdir(exist_ok=True)

# Load the ML model
try:
    embeddings = load_or_create_embeddings()
    print("✅ ML model loaded!")
except:
    embeddings = None
    print("❌ Failed to load ML model")

async def validate_image(file: UploadFile):
    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    print(f"✅ Saved file: {file.filename}")
    
    # Check if model loaded
    if embeddings is None:
        return {
            "status": "error",
            "similar_images": [],
            "message": "ML model not loaded"
        }
    
    # Find similar images using teammate's code
    try:
        results = find_similar_images(str(file_path), embeddings)
        
        # Format results
        similar_images = []
        for r in results[:5]:  # Top 5 only
            similar_images.append({
                "filename": r.get("filename", "unknown"),
                "similarity_score": r.get("score", 0.0)
            })
        
        # Clean up temp file
        file_path.unlink()
        
        return {
            "status": "success",
            "similar_images": similar_images
        }
        
    except Exception as e:
        return {
            "status": "error",
            "similar_images": [],
            "message": str(e)
        }