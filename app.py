from flask import Flask, render_template, request, jsonify, send_from_directory
import fiftyone as fo
import fiftyone.zoo as foz
import time
import os

app = Flask(__name__)

IMAGE_DIR = "data/validation/data"

# use fiftyone
try:
    dataset = foz.load_zoo_dataset(
        "open-images-v7",
        split="validation",
        dataset_dir="data",
        max_samples=100,  # limit for testing
    )
except KeyError as e:
    print(f"Error downloading dataset: {e}")
    dataset = None

images = []

if dataset: 
    dataset = dataset.shuffle()

    selected_samples = dataset.take(20)

    # prepare images for rendering
    for sample in dataset:
        image_path = sample.filepath
        image_filename = os.path.basename(image_path)

        if hasattr(sample, 'ground_truth') and sample.ground_truth.detections:
            label = sample.ground_truth.detections[0].label
        else:
            label = "No Label"
            
        images.append({
            "id": sample.id,
            "url": f"/images/{image_filename}",
            "label": label
        })

        print(f"Sample ID: {sample.id}, Label: {label}, Image Path: {image_path}")

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

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
