from flask import Flask, render_template, request, jsonify
import pandas as pd
import time

app = Flask(__name__)

images_df = pd.read_csv('data/images.csv')

user_interactions = []

@app.route('/')
def index():
    return render_template('index.html', images=images_df.to_dict(orient='records'))

@app.route('/interact', methods=['POST'])
def interact():
    data = request.get_json()
    data['timestamp'] = time.time()
    user_interactions.append(data)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
