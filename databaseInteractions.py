import sqlite3
from flask import g
# import logging

# logging.basicConfig(level=logging.DEBUG)

DATABASE = 'interactions.db'

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
            image_id TEXT NOT NULL,
            action TEXT NOT NULL,
            timestamp REAL NOT NULL,
            hover_time REAL,
            comment TEXT
        )
    ''')
    db.commit()
    # logging.debug("Database initialized.")

def save_interaction(data):
    db = get_db()
    cursor = db.cursor()
    # logging.debug(f"Saving interaction: {data}")
    cursor.execute('''
        INSERT INTO interactions (image_id, action, timestamp, hover_time, comment)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['image_id'], data['action'], data['timestamp'], data.get('hover_time'), data.get('comment')))
    db.commit()
    # logging.debug("Interaction saved.")

def get_interactions():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM interactions')
    return cursor.fetchall()

def calculate_score(interactions):
    score = 0
    weights = {
        'like': 3,
        'comment': 2,
        'hover': 1
    }

    for interaction in interactions:
        if interaction[2] == 'hover' and interaction[4]:  # hover action
            score += weights['hover'] * (interaction[4] / 1000)  # hover time weighted
        else:
            score += weights.get(interaction[2], 0)

    return score