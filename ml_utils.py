import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import GradientBoostingRegressor

# pretrained resnet50 for embeddings
# logistic regression for interactions as labels
# predict scores for new images based on users past

EMBEDDING_FILE = '/app/data/image_embeddings.pkl'
MODEL_FILE = '/app/data/recommender_model.pkl'

# Simple image transformation for extracting embeddings of images
image_transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406], 
        std=[0.229, 0.224, 0.225]
    )
])

def load_embedding_model():
    # Use pretrained resnet50 model and remove the final classification layer to make it for general purpose
    model = models.resnet50(pretrained=True)
    model = nn.Sequential(*list(model.children())[:-1])  # remove the last fc layer
    model.eval()
    return model

def extract_image_embedding(model, image_path):
    image = Image.open(image_path).convert('RGB')
    tensor = image_transform(image).unsqueeze(0)
    with torch.no_grad():
        embedding = model(tensor).numpy().flatten()
    return embedding

def generate_embeddings(image_dir, image_list):
    """
    Generate embeddings for all images and store in a dictionary.
    image_list: List of dicts with {"id": sample.id, "url": "...", "labels": "..."}
    """
    if os.path.exists(EMBEDDING_FILE):
        with open(EMBEDDING_FILE, 'rb') as f:
            embeddings = pickle.load(f)
    else:
        embeddings = {}

    model = load_embedding_model()
    
    for img in image_list:
        image_filename = img['url'].replace('/images/', '')
        if img['id'] not in embeddings:
            image_path = os.path.join(image_dir, image_filename)
            embedding = extract_image_embedding(model, image_path)
            embeddings[img['id']] = embedding

    with open(EMBEDDING_FILE, 'wb') as f:
        pickle.dump(embeddings, f)

def load_embeddings():
    with open(EMBEDDING_FILE, 'rb') as f:
        embeddings = pickle.load(f)
    return embeddings

def build_training_data(interactions, label_map, embeddings):
    """
    Build (X, y) for model training.
    - interactions: list of tuples from DB: (id, username, image_id, action, timestamp, hover_time, comment)
    - label_map: dict of image_id -> [labels]
    - embeddings: dict of image_id -> embedding vector
    """

    action_weights = {
        'like': 1.0,
        'comment': 0.8,
        'hover': 0.3
    }

    X = []
    y = []
    for interaction in interactions:
        # unpack the interaction
        _, username, image_id, action, _, hover_time, _ = interaction
        
        if image_id not in embeddings:
            continue

        # Weighted labels for specific action: Like > Comment > Hover
        label = action_weights.get(action, 0)  # Default to 0 for unknown actions
        emb = embeddings[image_id]

        hover_time_feature = [hover_time] if hover_time else [0]  # Add hover time, default to 0 if missing
        user_feature = [hash(username) % 1000]  # Hash username to numeric for modeling
        combined_features = np.concatenate([emb, hover_time_feature or [0], user_feature or [0]])

        X.append(combined_features)

        y.append(label)
        print("Embedding shape:", emb.shape)
        # print("Hover time feature:", hover_time_feature)
        
        print(f"Feature matrix shape: {X.shape}, Target shape: {y.shape}")

        # Check if empty training data
        if len(X) == 0 or len(y) == 0:
            raise ValueError("Training data is empty. Check interactions or embeddings.")

    return np.array(X), np.array(y)

def train_model(X, y):
    if len(X) < 10:  # Need enough data
        print("Not enough data to train model.")
        return
    model = GradientBoostingRegressor()
    model.fit(X, y)
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(model, f)
    print("Model trained and saved.")

def load_model():
    if not os.path.exists(MODEL_FILE):
        return None
    with open(MODEL_FILE, 'rb') as f:
        model = pickle.load(f)
    return model

def predict_scores(model, embeddings, image_ids):
    """
    Given a model and a list of image_ids, return predicted scores.
    """
    X = []
    for img_id in image_ids:
        if img_id in embeddings:
            emb = embeddings[img_id]
            hover_time_feature = [0]  # Default hover time to 0 for prediction
            combined_features = np.concatenate([emb, hover_time_feature])
            X.append(combined_features)
        else:
            # Use zero vector for missing embeddings
            X.append(np.zeros((2049,)))  # ResNet50 embedding size + hover time
    X = np.array(X)
    scores = model.predict(X)  # Predict scores
    return scores
