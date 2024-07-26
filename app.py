from flask import Flask, render_template, request, jsonify
import fiftyone as fo
import fiftyone.zoo as foz
import time
import os

app = Flask(__name__)

# Load a smaller split of the Open Images dataset v7 using FiftyOne
dataset = foz.load_zoo_dataset(
    "open-images-v7",
    split="validation",
    max_samples=20,  # Limit to 20 images for testing
)
images = []



# Prepare images for rendering
for sample in dataset:
    # Check if 'ground_truth' exists and contains detections
    image_path = sample.filepath
    if hasattr(sample, 'ground_truth') and sample.ground_truth.detections:
        label = sample.ground_truth.detections[0].label
    else:
        label = "No Label"
    images.append({
        "id": sample.id,
        "filepath": image_path,
        "label": label
    })

    print(f"Sample ID: {sample.id}, Label: {label}")

user_interactions = []

@app.route('/')
def index():
    return render_template('index.html', images=images)

@app.route('/interact', methods=['POST'])
def interact():
    data = request.get_json()
    data['timestamp'] = time.time()
    user_interactions.append(data)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
