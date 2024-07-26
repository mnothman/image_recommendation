from flask import Flask, render_template, request, jsonify
import pandas as pd
import time
import tensorflow as tf
import tensorflow_datasets as tfds
import base64

# print(tfds.list_builders())


app = Flask(__name__)

# dataset = tfds.load('open_images/v7', split='train')
dataset = tfds.load('open_images_v4', split='validation')

images = []

for datum in dataset.take(20): #limit to 20 images for now
    image = datum["image"].numpy()
    _, buffer = tf.image.encode_jpeg(image).numpy()
    image_url = base64.b64encode(buffer).decode('utf-8')
    images.append({
        'url': f'data:image/jpeg;base64,{image_url}',
        'id': datum["image/id"].numpy().decode('utf-8'),
        'label': datum["objects"]["label"].numpy().tolist()
    })
    print(f'Loaded image {datum["image/id"].numpy().decode("utf-8")}')

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
