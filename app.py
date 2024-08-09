from flask import Flask, render_template, request, jsonify, send_from_directory, g, redirect, url_for, session
import fiftyone as fo
import fiftyone.zoo as foz
import time
import os
from fiftyone import ViewField as F
import databaseInteractions
from databaseInteractions import calculate_score
from cleanup import cleanup_old_images # 1/2 Remove later when hosting 

app = Flask(__name__)
app.secret_key = 'testKey'

IMAGE_DIR = "data/validation/data"



@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_databaseInteractions', None)
    if db is not None:
        db.close()

print("Downloading dataset...")


#sort reset for algorithm every week or so. if someone hates dogs show them a dog pic or two to see if they still hate dogs. 
#not interested button for pics (get the negative labels of those images)

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

        
@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    # fetch settings
    user = databaseInteractions.get_user(session['username'])
    # fix error TypeError: 'NoneType' object is not subscriptable when logging back in after restart app
    if not user:
        session.pop('username', None)  # Clear the session
        return redirect(url_for('login'))

    safe_search = user[4] == 1  # safe_search is the 5th column in the users table
    filtered_images = images
    if safe_search:
        filtered_images = [img for img in images if 'unsafe' not in img['labels'].lower()]
    return render_template('index.html', images=filtered_images)

@app.route('/recommendations')
def recommendations():
    if 'username' not in session:
        return redirect(url_for('login'))

    interactions = databaseInteractions.get_interactions()
    label_map = {image['id']: image['labels'].split('; ') for image in images}

    filtered_interactions = [
        interaction for interaction in interactions
        if interaction[2] in label_map and label_map[interaction[2]] != ["No Labels"]
    ]

    label_scores = calculate_score(interactions, label_map)
    
    # rank images based on cumulative label scores
    sorted_images = sorted(images, key=lambda img: sum(label_scores.get(label, 0) for label in img['labels'].split('; ')), reverse=True)
    
    return render_template('recommendations.html', images=sorted_images, interactions=filtered_interactions, label_scores=label_scores)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        databaseInteractions.save_user(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = databaseInteractions.get_user(username)
        if user and user[2] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = "Invalid username or password."
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/interact', methods=['POST'])
def interact():
    data = request.get_json()
    data['timestamp'] = time.time()
    data['username'] = session.get('username')
    databaseInteractions.save_interaction(data)
    return jsonify({"status": "success"})

@app.route('/images/<filename>')
def serve_image(filename):
    return send_from_directory(IMAGE_DIR, filename)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        safe_search = 'safe_search' in request.form
        preferences = request.form.get('preferences', '')
        databaseInteractions.update_user_preferences(session['username'], preferences, 1 if safe_search else 0)
        return redirect(url_for('index'))
    user = databaseInteractions.get_user(session['username'])
    return render_template('settings.html', safe_search=user[4], preferences=user[3])

if __name__ == '__main__':
    with app.app_context():
        databaseInteractions.init_db()
        cleanup_old_images(IMAGE_DIR, threshold_days=2)  # 2/2 Remove later when hosting db
    fo.launch_app(dataset)
    fo.pprint(dataset.stats(include_media=True))
    app.run(host='0.0.0.0', port=5000)