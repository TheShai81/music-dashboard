import mysql.connector
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


def get_connection():
    """
    Establish and return a MySQL database connection.

    Uses environment variables from .env file if available, otherwise falls back to defaults.
    Each team member should create a .env file with their local MySQL credentials.
    """
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "spotify_user"),
        password=os.getenv("DB_PASSWORD", "Spotify123!"),
        database=os.getenv("DB_NAME", "spotify_db")
    )
    return conn

