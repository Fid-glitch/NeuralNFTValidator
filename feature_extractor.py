import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import pickle
from tqdm import tqdm

print("Starting feature extraction...")

# Select device (GPU if available, else CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)

# Load pretrained ResNet50
model = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
model = torch.nn.Sequential(*list(model.children())[:-1])  # Remove final layer
model.to(device)
model.eval()

# Image preprocessing
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
])

# Dataset path
dataset_path = "dataset/originals"

embeddings = {}

# Walk through all subfolders
for root, dirs, files in os.walk(dataset_path):
    for file in files:
        if file.lower().endswith("_os.png"):
            img_path = os.path.join(root, file)

            try:
                image = Image.open(img_path).convert("RGB")
                image = transform(image).unsqueeze(0).to(device)

                with torch.no_grad():
                    feature = model(image)
                    feature = feature.cpu().numpy().flatten()

                embeddings[img_path] = feature

            except Exception as e:
                print(f"Error processing {img_path}: {e}")

# Create embeddings folder
os.makedirs("embeddings", exist_ok=True)

# Save embeddings
with open("embeddings/embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)

print("\nTotal images processed:", len(embeddings))
print("Embeddings saved successfully!")