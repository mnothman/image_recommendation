import sqlite3
from flask import g
# import logging

# logging.basicConfig(level=logging.DEBUG)

#creates db in folder data
DATABASE = '/app/data/interactions.db'

def get_db():
    db = getattr(g, '_databaseInteractions', None)
    if db is None:
        db = g._databaseInteractions = sqlite3.connect(DATABASE)
    return db

def init_db():
    db = get_db()
    cursor = db.cursor()
    # logging.debug("Creating interactions table if it doesn't exist.")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            image_id TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp REAL NOT NULL,
            hover_time REAL,
            comment TEXT
        )
    ''')
    # users table with preferences and safe_search
    # safe_search at [4] is connected to app.py route ('/') line safe_search = user[4] == 1 
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            preferences TEXT,
            safe_search INTEGER DEFAULT 0 
        )
    ''')
    # table for labels and scores
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS label_scores (
            username TEXT NOT NULL,
            label TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            PRIMARY KEY (username, label)
        )
    ''')
    db.commit()
    # logging.debug("Database initialized.")

# def save_interaction(data):
#     db = get_db()
#     cursor = db.cursor()
#     # logging.debug(f"Saving interaction: {data}")
#     cursor.execute('''
#         INSERT INTO interactions (username, image_id, action, timestamp, hover_time, comment)
#         VALUES (?, ?, ?, ?, ?, ?)
#     ''', (data['username'], data['image_id'], data['action'], data['timestamp'], data.get('hover_time'), data.get('comment')))
#     db.commit()
#     # logging.debug("Interaction saved.")


def save_interaction(data, label_map):
    db = get_db()
    cursor = db.cursor()

    # check if the interaction is a "like" or "click"
    if data['action'] in ['like', 'click']:
        # check if a like or click already exists for this user and image
        cursor.execute('''
            SELECT id FROM interactions WHERE username = ? AND image_id = ? AND action = ?
        ''', (data['username'], data['image_id'], data['action']))
        result = cursor.fetchone()

        if result:
            # can update existing like / clicks 
            cursor.execute('''
                UPDATE interactions
                SET timestamp = ?, hover_time = ?, comment = ?
                WHERE id = ?
            ''', (data['timestamp'], data.get('hover_time'), data.get('comment'), result[0]))
        else:
            cursor.execute('''
                INSERT INTO interactions (username, image_id, action, timestamp, hover_time, comment)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['username'], data['image_id'], data['action'], data['timestamp'], data.get('hover_time'), data.get('comment')))
    else: #comments can have unlimited, likes only one
        cursor.execute('''
            INSERT INTO interactions (username, image_id, action, timestamp, hover_time, comment)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['username'], data['image_id'], data['action'], data['timestamp'], data.get('hover_time'), data.get('comment')))

    db.commit()
    # update label scores
    if data['image_id'] in label_map:
        labels = label_map[data['image_id']]
        update_label_scores(data['username'], labels, data['action'], data.get('hover_time'))

    db.commit()
    
# function that updates label scores based on interactions in DB so that it is persistent
def update_label_scores(username, labels, action, hover_time=None):
    db = get_db()
    cursor = db.cursor()
    
    weights = {
        'like': 3,
        'comment': 2,
        'hover': 1
    }
    
    score_increment = weights.get(action, 0)
    if action == 'hover' and hover_time:
        score_increment = weights['hover'] * (hover_time / 1000)

    
    for label in labels:
        cursor.execute('''
            INSERT INTO label_scores (username, label, score)
            VALUES (?, ?, ?)
            ON CONFLICT(username, label) DO UPDATE SET
            score = score + excluded.score
        ''', (username, label, score_increment))
    
    db.commit()
# fetch label scores when generating recommendations
def get_user_label_scores(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT label, score FROM label_scores WHERE username = ?', (username,))
    return dict(cursor.fetchall())

#clears all recommendations and then recommendations page will be empty until more interactions are tracked
def clear_user_recommendations(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM label_scores WHERE username = ?', (username,))
    cursor.execute('DELETE FROM interactions WHERE username = ?', (username,))
    db.commit()


def get_interactions(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM interactions WHERE username = ?', (username,))
    return cursor.fetchall()

def save_user(username, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO users (username, password)
        VALUES (?, ?)
    ''', (username, password))
    db.commit()

def get_user(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cursor.fetchone()

def update_user_preferences(username, preferences, safe_search):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE users
        SET preferences = ?, safe_search = ?
        WHERE username = ? 
    ''', (preferences, safe_search, username))
    db.commit()

def calculate_score(interactions, label_map): #calc scores based on interactions. Interactions is a list of interactions, label_map is a dictionary of image_id to labels
    # Return is dictionary with labels as keys and their calculated scores as values.
    label_scores = {}
    weights = {
        'like': 3,
        'comment': 2,
        'hover': 1
        #clicks have no weight
    }
    # iterate thru interactions for scores of each label
    for interaction in interactions:
        image_id = interaction[2]
        action = interaction[3]
        hover_time = interaction[5]
        
        if image_id in label_map:
            labels = label_map[image_id]
            for label in labels:
                if label not in label_scores:
                    label_scores[label] = 0
                
                # Add the score based on action
                if action == 'hover' and hover_time:
                    label_scores[label] += weights['hover'] * (hover_time / 1000)  # hover time weight
                else:
                    label_scores[label] += weights.get(action, 0)

    return label_scores