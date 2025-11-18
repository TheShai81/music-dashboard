# App Directory – Spotify Dashboard Web Application

This folder contains the **application layer** of the project:  
a lightweight web interface that sits on top of the MySQL database created in `schema/`.

The app will eventually allow users to:
- View artists, tracks, genres, and musical attributes  
- Explore their listening insights  
- Run advanced queries (e.g., “songs similar to X”)  
- Interact with comments, likes, and preferences  
- Navigate a dashboard built on top of our ETL-loaded database

This directory will house the Python web framework code (Flask or Django).

---

## 1. Folder Purpose

The `app/` directory contains:

- **Application logic** (query functions, helpers)
- **Web routes** (Flask) or **views/URLs** (Django)
- **Templates** (HTML/Jinja2)
- **Static files** (CSS/JS), if needed
- **Database connection utilities**

This layer communicates directly with the database initialized in Step 3 of the project.

---

## 2. Planned Structure (Subject to Change)

A likely final structure (depending on Flask/Django decision):

### **If Flask:**
```text
app/
  __init__.py            # App factory + DB connection
  routes.py              # All endpoints
  queries.py             # Query logic using SQL
  db.py                  # Reusable DB connector
  templates/
    index.html
    artist.html
    track.html
    dashboard.html
  static/
    styles.css
    script.js
  README.md
```

### **If Django:**
```text
app/
  spotify_app/
    models.py
    views.py
    urls.py
    templates/
    static/
  manage.py
  README.md
```

<!-- All database conection parameters come from the project root .env file:  -->

DB_HOST=localhost
DB_PORT=3306
DB_NAME=spotify_db
DB_USER=spotify_user
DB_PASSWORD=Spotify123!


<!-- The app should load these values using python-dotenv: -->
from dotenv import load_dotenv
import os
import mysql.connector

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
)