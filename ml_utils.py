import os
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression

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
    X = []
    y = []
    for interaction in interactions:
        # unpack the interaction
        _, username, image_id, action, _, hover_time, _ = interaction
        
        if image_id not in embeddings:
            continue

        # Simple binary labels, 1 for positive actions (like, comment, but not hovers for now), and 0 for everything else
        # Can adjust later if needed
        positive_actions = ['like', 'comment']
        label = 1 if action in positive_actions else 0
        
        # Ignore hover_time for now since we don't consider it important feature for training. Store as X for now.
        
        emb = embeddings[image_id]
        X.append(emb)
        y.append(label)

    return np.array(X), np.array(y)

def train_model(X, y):
    if len(X) < 10:  # Need enough data
        print("Not enough data to train model.")
        return
    model = LogisticRegression(max_iter=1000)
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
            X.append(embeddings[img_id])
        else:
            # Use zero vector for missing embeddings
            X.append(np.zeros((2048,)))  # ResNet50 embedding size
    X = np.array(X)
    scores = model.predict_proba(X)[:, 1]  # Probability of class=1 which would be positive
    return scores
