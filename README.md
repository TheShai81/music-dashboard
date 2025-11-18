# spotify-dashboard
Git repo for Databases project

# Spotify Dashboard (Non-Streaming)

Relational database + mini-app built on top of Kaggle’s Spotify dataset.  
Users can create accounts, make friends, build playlists, and explore tracks, 
artists, and genres without actually streaming audio.

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
