import os
import pickle
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from torchvision.models import ResNet50_Weights
from PIL import Image
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

print("Loading model...")

weights = ResNet50_Weights.DEFAULT
model = models.resnet50(weights=weights)

model = nn.Sequential(*list(model.children())[:-1])
model.eval()

transform = weights.transforms()

print("Loading stored embeddings...")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "embeddings", "embeddings.pkl"), "rb") as f:
    stored_embeddings = pickle.load(f)

print("Total stored NFTs:", len(stored_embeddings))


def extract_feature(image_path):
    image = Image.open(image_path).convert("RGB")
    image = transform(image).unsqueeze(0)

    with torch.no_grad():
        feature = model(image)

    feature = feature.squeeze().numpy()
    return feature


def find_similar(query_image_path, top_k=5):
    query_feature = extract_feature(query_image_path)

    similarities = []

    for path, stored_feature in stored_embeddings.items():
        sim = cosine_similarity(
            query_feature.reshape(1, -1),
            stored_feature.reshape(1, -1)
        )[0][0]

        similarities.append((path, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)

    return similarities[:top_k]


if __name__ == "__main__":
    base_folder = os.path.join(BASE_DIR, "dataset", "originals", "witch_images")

    if not os.path.exists(base_folder):
        raise Exception(f"Folder not found: {base_folder}")

    first_folder = sorted(os.listdir(base_folder))[0]
    first_folder_path = os.path.join(base_folder, first_folder)

    first_image = os.listdir(first_folder_path)[0]
    query_image = os.path.join(first_folder_path, first_image)

    print("Testing image:", query_image)

    results = find_similar(query_image)

    print("\nTop 5 Similar NFTs:\n")
    for path, score in results:
        print(f"{path}  |  Similarity Score: {score:.4f}")