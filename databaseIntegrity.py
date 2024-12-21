from app import app  # Import the Flask app instance
from databaseInteractions import get_db

with app.app_context():  # Set up the application context
    db = get_db()
    cursor = db.cursor()

    # Check interactions table schema
    cursor.execute("PRAGMA table_info(interactions);")
    print("Interactions Table Schema:", cursor.fetchall())

    # Check users table schema
    cursor.execute("PRAGMA table_info(users);")
    print("Users Table Schema:", cursor.fetchall())

    # Check label_scores table schema
    cursor.execute("PRAGMA table_info(label_scores);")
    print("Label Scores Table Schema:", cursor.fetchall())

    # Validate data in interactions
    cursor.execute("SELECT * FROM interactions;")
    print("Interactions Data:", cursor.fetchall())

    # Validate data in label_scores
    cursor.execute("SELECT * FROM label_scores;")
    print("Label Scores Data:", cursor.fetchall())

    # Validate data in users
    cursor.execute("SELECT * FROM users;")
    print("Users Data:", cursor.fetchall())
