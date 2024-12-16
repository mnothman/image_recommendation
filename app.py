from flask import Flask, render_template, request, jsonify, send_from_directory, g, redirect, url_for, session
import fiftyone as fo
import fiftyone.zoo as foz
import time
import os
from fiftyone import ViewField as F
import databaseInteractions
from databaseInteractions import calculate_score
from cleanup import cleanup_old_images # 1/2 Remove later when hosting 
from ml_utils import generate_embeddings, load_embeddings, load_model, predict_scores, build_training_data, train_model

app = Flask(__name__)
app.secret_key = 'testKey'

IMAGE_DIR = "data/validation/data"

UNSAFE_LABELS = ["nudity", "violence", "blood", "gore", "hate", "hate speech", "racism", "bra", "injury", "wound", "gun", "weapon", "knife", "firearm", "explosive", "bomb", "underwear", "lingerie", "swimsuit", "bikini", "brassiere", "bra", "panties", "thong", "nipple", "breast", "naked", "smoking", "drinking", "alcohol"]

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

# Create embeddings for images after loading the dataset
if images:
    generate_embeddings(IMAGE_DIR, images)

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
        filtered_images = [
            img for img in images 
            if not any(unsafe in img['labels'].lower() for unsafe in UNSAFE_LABELS)
        ]
    # old safe search without UNSAFE_LABELS list, implement later if there is something built in already 
    # if safe_search:
    #     filtered_images = [img for img in images if 'unsafe' not in img['labels'].lower()]
    return render_template('index.html', images=filtered_images)

@app.route('/recommendations')
def recommendations():
    if 'username' not in session:
        return redirect(url_for('login'))

    # fetch settings for user
    user = databaseInteractions.get_user(session['username'])
    safe_search = user[4] == 1


    interactions = databaseInteractions.get_interactions(session['username']) # fetch interactions from DB based on username
    # print("Interactions fetched from DB:", interactions) 
    if not interactions: # stop recommendations.html from displaying deleted interactions with just 0 scores in them
        return render_template('recommendations.html', images=[], interactions=[], label_scores={})

    
    label_map = {image['id']: image['labels'].split('; ') for image in images}

# # manual label scoring method before machine learning model:
    # filtered_interactions = [ # filter out interactions with no positive labels
    #     interaction for interaction in interactions
    #     if interaction[2] in label_map and label_map[interaction[2]] != ["No Labels"]
    # ]

    # # calculate label scores and update users label preferences
    # label_scores = databaseInteractions.calculate_score(filtered_interactions, label_map)
    
    # # retrieve label scores stored in db for the user
    # stored_label_scores = databaseInteractions.get_user_label_scores(session['username'])

    # # merge in session labels with current stores ones IMPORTANT
    # for label, score in label_scores.items():
    #     if label in stored_label_scores:
    #         stored_label_scores[label] += score
    #     else:
    #         stored_label_scores[label] = score

    # # rank images based on cumulative label scores
    # sorted_images = sorted(images, key=lambda img: sum(stored_label_scores.get(label, 0) for label in img['labels'].split('; ')), reverse=True)
    


# Instead of just label scoring, use the trained ML model:

    embeddings = load_embeddings()

    model = load_model()


   # If model is not trained yet, fall back to old method
    if model is None:
        # old method:
        filtered_interactions = [
            interaction for interaction in interactions
            if interaction[2] in label_map and label_map[interaction[2]] != ["No Labels"]
        ]
        label_scores = databaseInteractions.calculate_score(filtered_interactions, label_map)
        stored_label_scores = databaseInteractions.get_user_label_scores(session['username'])
        # merge
        for label, score in label_scores.items():
            if label in stored_label_scores:
                stored_label_scores[label] += score
            else:
                stored_label_scores[label] = score

        # sort images by label scores
        sorted_images = sorted(images, key=lambda img: sum(stored_label_scores.get(label, 0) for label in img['labels'].split('; ')), reverse=True)
    else:
        # use ML model to predict scores
        image_ids = [img['id'] for img in images]
        scores = predict_scores(model, embeddings, image_ids)
        # pair images with scores
        image_score_pairs = list(zip(images, scores))
        # sort by predicted probability of positive engagement
        sorted_images = sorted(image_score_pairs, key=lambda x: x[1], reverse=True)
        sorted_images = [x[0] for x in sorted_images]  # extract images

        # no label scores needed when using ML model but still store for debug
        stored_label_scores = {}

        # print scores for training model
        scores = predict_scores(model, embeddings, image_ids)
        print("Predicted scores:", list(zip(image_ids, scores)))

    if safe_search:
        sorted_images = [
            img for img in sorted_images 
            if not any(unsafe in img['labels'].lower() for unsafe in UNSAFE_LABELS)
        ]

    # return render_template('recommendations.html', images=sorted_images, interactions=filtered_interactions, label_scores=stored_label_scores)
    return render_template('recommendations.html', images=sorted_images, interactions=interactions, label_scores=stored_label_scores)

@app.route('/train_model')
def train_ml_model():
    if 'username' not in session:
        return "Please log in to train model."
    
    # Fetch all user interactions from all the users to build global model 
    db = g._databaseInteractions if hasattr(g, '_databaseInteractions') else databaseInteractions.get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM interactions')
    all_interactions = cursor.fetchall()

    label_map = {image['id']: image['labels'].split('; ') for image in images}
    embeddings = load_embeddings()

    X, y = build_training_data(all_interactions, label_map, embeddings)
    train_model(X, y)
    return "Model trained!"

# temporary for model debugging
@app.route('/debug_model')
def debug_model():
    import pickle
    MODEL_FILE = '/app/data/recommender_model.pkl'
    try:
        with open(MODEL_FILE, 'rb') as f:
            trained_model = pickle.load(f)
        return f"Coefficients: {trained_model.coef_}, Intercept: {trained_model.intercept_}"
    except FileNotFoundError:
        return "Model file not found. Train the model first."

#clears all recommendations and then recommendations page will be empty until more interactions are tracked
@app.route('/clear_recommendations')
def clear_recommendations():
    if 'username' not in session:
        return redirect(url_for('login'))

    # clear the user's label scores using the clear_user_recommendations function in databaseinteractions.py
    databaseInteractions.clear_user_recommendations(session['username'])

    return redirect(url_for('recommendations'))

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

    # pass label_map to save_interaction
    label_map = {image['id']: image['labels'].split('; ') for image in images}
    databaseInteractions.save_interaction(data, label_map)

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
    # fo.launch_app(dataset)
    fo.launch_app(dataset, remote=True, address="0.0.0.0", port=5151)
    fo.pprint(dataset.stats(include_media=True))
    app.run(host='0.0.0.0', port=5000)