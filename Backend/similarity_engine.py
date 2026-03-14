from similarity import find_similar

def find_similar_images(file_path, embeddings=None):
    results = find_similar(file_path)
    
    return [
        {
            "filename": path.split("\\")[-1].split("/")[-1],
            "score": float(score),
            "image_url": "http://127.0.0.1:8000/dataset/" + path.replace("\\", "/").split("dataset/")[-1]
        }
        for path, score in results
    ]