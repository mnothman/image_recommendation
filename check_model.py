import pickle

MODEL_FILE = "/app/data/recommender_model.pkl"

with open(MODEL_FILE, 'rb') as f:
    trained_model = pickle.load(f)

# For logistic regression model:
print("Model Coefficients:", trained_model.coef_)
print("Model Intercept:", trained_model.intercept_)
