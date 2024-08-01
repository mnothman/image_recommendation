from flask import Flask, render_template, request, jsonify, send_from_directory
import fiftyone as fo
import fiftyone.zoo as foz
import time
import os
from fiftyone import ViewField as F

app = Flask(__name__)

IMAGE_DIR = "data/validation/data"


#docs: https://voxel51.com/blog/exploring-google-open-images-v7/
#https://docs.voxel51.com/user_guide/using_datasets.html#labels
#https://docs.voxel51.com/user_guide/using_datasets.html#metadata
# use fiftyone
try:
    dataset = foz.load_zoo_dataset(
        "open-images-v7",
        split="validation",
        dataset_dir="data",
        max_samples=100,  # limit for testing
        label_types=["classifications"],
        shuffle=True,
    )
except KeyError as e:
    print(f"Error downloading dataset: {e}")
    dataset = None

#https://stackoverflow.com/questions/70274971/exclude-certain-classes-when-loading-dataset-with-fiftyone

images = []


# neg_view = dataset.filter_labels("negative_labels", F("label")=="Person")
# print("negative view count:", neg_view.count())
# # print("neg view count classifications:", neg_view.values("classifications"))
# print("all neg views: ", neg_view)

if dataset:
    selected_samples = dataset.take(50)

    # # prepare images for rendering
    for sample in selected_samples:
        image_path = sample.filepath
        image_filename = os.path.basename(image_path)

        labels = []

        if sample.has_field("positive_labels") and sample.positive_labels is not None:
            for classification in sample.positive_labels.classifications:
                labels.append(classification.label)

        labels_str = "; ".join(labels) if labels else "No Labels"

        print(f"Sample ID: {sample.id}, Positive Labels: {labels_str}, Image Path: {image_path}")


        images.append({
            "id": sample.id,
            "url": f"/images/{image_filename}",
            "labels": labels_str
        })

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
    fo.launch_app(dataset)
    fo.pprint(dataset.stats(include_media=True))
    app.run(host='0.0.0.0', port=5000)