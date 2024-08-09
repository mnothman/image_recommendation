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
    db.commit()
    # logging.debug("Database initialized.")

def save_interaction(data):
    db = get_db()
    cursor = db.cursor()
    # logging.debug(f"Saving interaction: {data}")
    cursor.execute('''
        INSERT INTO interactions (username, image_id, action, timestamp, hover_time, comment)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['username'], data['image_id'], data['action'], data['timestamp'], data.get('hover_time'), data.get('comment')))
    db.commit()
    # logging.debug("Interaction saved.")

def get_interactions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM interactions')
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