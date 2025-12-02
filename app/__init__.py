from flask import Flask
from dotenv import load_dotenv
from pathlib import Path
import os
import mysql.connector
from mysql.connector import Error

# load database connection keys/info
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path)

def create_app():
    app = Flask(__name__)
    app.secret_key = "dev"  # dev key for now since this isn't some secure production app

    # database config
    app.config['DB_HOST'] = os.getenv("DB_HOST")
    app.config['DB_USER'] = os.getenv("DB_USER")
    app.config['DB_PASSWORD'] = os.getenv("DB_PASSWORD")
    app.config['DB_NAME'] = os.getenv("DB_NAME")

    # connect DB to app
    try:
        app.db = mysql.connector.connect(
            host=app.config['DB_HOST'],
            user=app.config['DB_USER'],
            password=app.config['DB_PASSWORD'],
            database=app.config['DB_NAME']
        )
        print("Connected to MySQL database successfully.")
    except Error as e:
        print(f"Error connecting to MySQL: {e}")

    from .routes import bp
    app.register_blueprint(bp)

    return app
