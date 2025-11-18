# spotify-dashboard
Git repo for Databases project

# Spotify Dashboard (Non-Streaming)

Relational database + mini-app built on top of Kaggle’s Spotify dataset.  
Users can create accounts, make friends, build playlists, and explore tracks, 
artists, and genres without actually streaming audio.

## PRELIMINARY PROJECT STEPS
1. Create directory in your computer
2. Run: git clone https://github.com/egrantcharov/spotify-dashboard.git
3. Set up virtual machine (python3 -m venv venv   |   source venv/bin/activate)
4. Run: pip install -r requirements.txt
5. Run the Schema: mysql -u root -p < schema/schema.sql
6. Create .env: cp .env.example .env
7. Verify Database Setup: mysql -u spotify_user -p spotify_db
8. In MySQL shell: SHOW TABLES;
9. Data Loading (Lucas)
10. Backend (Shailesh)
11. GUI (Ryan)

## 1. Project Overview

This project demonstrates:

- Proper **relational schema design** (3NF-ish, foreign keys, constraints)
- **Data loading** from CSV into SQL using Python scripts
- Support for typical music-app operations:
  - Users, friendships, subscriptions
  - Artists, tracks, genres
  - Playlists and playlist membership
  - (Later) a small web UI / API on top of the database

**Data source:**  
Kaggle – “Spotify Datasets”  
(artists + tracks CSVs)

## 2. Tech Stack

- **Database:** MySQL
- **Language:** Python 3.x for generating and loading data
- **Future app:** Flask or Django (TBD)
- **Version control:** Git + GitHub

## 3. Repository Structure

```text
spotify-dashboard/
  schema/
    schema.sql            # EVERYONE CREATE TABLE LOCALLY FOR TESTING; 
                          # statements + constraints

  data/
    artists.csv           # Raw Kaggle artists data
    tracks.csv            # Raw Kaggle tracks data

  generate_load_data/
    load_artists.py       # Extract artists.csv, transform, load into DB
    load_tracks.py        # Extract tracks.csv, transform, load into DB
    generate_fake_users.py # Create synthetic users, friendships, playlists etc.

  app/
    # Placeholder for a future Flask/Django app (routes, models, templates...)

  .env.example            # Example environment variables; copy to .env locally
  README.md               # This file