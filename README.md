# spotify-dashboard
Git repo for Databases project

# Spotify Dashboard (Non-Streaming)

Relational database + mini-app built on top of Kaggle’s Spotify dataset.
Users can create accounts, make friends, build playlists, and explore tracks,
artists, and genres without actually streaming audio.

## Quick Start

1. **Clone repository**: `git clone https://github.com/egrantcharov/spotify-dashboard.git`
2. **Set up Python environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Download data files** (see Data Setup section) - place `artists.csv` and `tracks.csv` in `data/SpotifyKaggle/`
4. **Set up database**:
   ```bash
   # Option A: MySQL CLI
   mysql -u root -p < schema/schema.sql

   # Option B: Python script (if MySQL CLI unavailable)
   python setup_db.py
   ```
5. **Configure database connection**: `cp .env.example .env` then edit `.env` with your MySQL credentials
6. **Verify setup**: `python test_connection.py`
7. **Load data** (see Data Loading section below)

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
Kaggle – "Spotify Datasets"
https://www.kaggle.com/datasets/lehaknarnauli/spotify-datasets

**Note:** The data files are too large to include in git. Each team member must download them locally (see Data Setup section below).

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
    db_config.py          # Database connection helper
    load_artists.py       # Extract artists.csv, transform, load into DB
    load_tracks.py        # Extract tracks.csv, transform, load into DB
    generate_fake_users.py # Create synthetic users, preferences, subscriptions, etc.
    load_fake_users.py    # Load synthetic user data into database

  setup_db.py            # Alternative script to create database schema (if MySQL CLI unavailable)
  test_connection.py     # Script to verify database connection and show table counts

  processed/              # Generated CSV files (created by generate_fake_users.py)
    users.csv
    preferences.csv
    subscriptions.csv
    comments.csv
    track_likes.csv

  app/
    # Placeholder for a future Flask/Django app (routes, models, templates...)

  .env.example            # Example environment variables; copy to .env locally
  README.md               # This file

## 4. Data Setup

### Downloading Data Files

The Spotify datasets are too large to include in git. Each team member must download them locally:

1. **Go to Kaggle**: https://www.kaggle.com/datasets/lehaknarnauli/spotify-datasets
2. **Download the following files**:
   - `artists.csv` (~1.1M rows)
   - `tracks.csv` (~586K rows)
3. **Create the directory structure**:
   ```bash
   mkdir -p data/SpotifyKaggle
   ```
4. **Place the downloaded files** in `data/SpotifyKaggle/`:
   ```bash
   data/SpotifyKaggle/
     artists.csv
     tracks.csv
   ```

### Database Configuration

1. Copy `.env.example` to `.env`: `cp .env.example .env`
2. Edit `.env` with your MySQL credentials (use `root` or `spotify_user` depending on your setup)
3. Scripts automatically use `.env` values, or fall back to defaults if `.env` doesn't exist

**Note**: `.env` is gitignored - each team member uses their own local credentials.

## 5. Data Loading Instructions

### Prerequisites
- Database schema created (see Quick Start #4)
- Virtual environment activated
- Data files in `data/SpotifyKaggle/` (artists.csv, tracks.csv)
- `.env` file configured

**Run all scripts from `generate_load_data/` directory.**

### Loading Steps

**Step 1: Load Artists and Genres**
```bash
cd generate_load_data
python load_artists.py
```
Loads ~1.1M artists, ~5.4K genres, and relationships. Runtime: ~5-10 minutes.

**Step 2: Load Tracks**
```bash
python load_tracks.py
```
Loads ~586K tracks with normalized musical attributes. Runtime: ~10-15 minutes.

**Step 3: Generate Fake User Data**
```bash
python generate_fake_users.py [num_users]
```
Generates synthetic users, preferences, subscriptions, comments, and likes. Default: 1000 users. Creates CSV files in `processed/` directory. Runtime: ~1-2 minutes.

**Step 4: Load Fake User Data**
```bash
python load_fake_users.py
```
Loads user data from `processed/` directory in correct order (respects foreign keys). Runtime: ~2-5 minutes.

### Complete Loading Sequence
```bash
cd generate_load_data
python load_artists.py
python load_tracks.py
python generate_fake_users.py 1000
python load_fake_users.py
```

### Verify Data Load
```bash
python test_connection.py  # Shows table counts
```

**Expected counts:**
- Artists: ~1,104,349
- Genres: ~5,365
- ArtistGenres: ~460,843
- Tracks: ~586,672
- TrackArtists: ~730,141
- Users/Comments/Likes: Depends on `num_users` you generated

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Unknown database 'spotify_db'" | Run schema setup (Quick Start #4) |
| "ModuleNotFoundError: No module named 'mysql'" | Activate venv and run `pip install -r requirements.txt` |
| MySQL CLI not found | Use `python setup_db.py` instead |
| Tracks loading stops | Clear and reload: `TRUNCATE TABLE Tracks; TRUNCATE TABLE TrackArtists;` then rerun `load_tracks.py` |

## Notes

- **Data Normalization**: Musical attributes (loudness, tempo, key) normalized to [0,1] range
- **Time Signature**: Stored as integer 0-5 (number of beats per bar, 0=unknown)
