# spotify-dashboard
Git repo for Databases project

# Spotify Dashboard (Non-Streaming)

Relational database + mini-app built on top of Kaggle’s Spotify dataset.
Users can create accounts, make friends, build playlists, and explore tracks,
artists, and genres without actually streaming audio.

## PRELIMINARY PROJECT STEPS
1. Create directory in your computer
2. Run: `git clone https://github.com/egrantcharov/spotify-dashboard.git`
3. Set up virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies: `pip install -r requirements.txt`
5. **Download data files locally** (see Data Setup section below)
6. **Set up database schema** (choose one method):
   - **Option A (MySQL CLI)**: `mysql -u root -p < schema/schema.sql`
   - **Option B (Python script)**: `python setup_db.py` (if MySQL CLI not available)
7. Create `.env` file: `cp .env.example .env` and update with your local MySQL credentials
8. Verify Database Setup: Run `python test_connection.py` or connect via MySQL CLI
9. Data Loading (see Data Loading section below)
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

Each team member should configure their local MySQL connection:

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** with your local MySQL credentials:
   ```bash
   DB_HOST=localhost
   DB_USER=spotify_user          # or your MySQL username
   DB_PASSWORD=Spotify123!      # or your MySQL password
   DB_NAME=spotify_db            # or your database name
   ```

3. **The scripts will automatically use these values** from the `.env` file. If `.env` doesn't exist, they'll fall back to defaults (which match the schema.sql setup).

**Important**: The `.env` file is gitignored and won't be committed, so each person can have their own local configuration.

## 5. Data Loading Instructions

### Prerequisites
- MySQL database must be set up and running
- Schema must be created (see Preliminary Project Steps #6)
- Virtual environment activated (`source venv/bin/activate`)
- Python dependencies installed (`pip install -r requirements.txt`)
- **Data files downloaded** and placed in `data/SpotifyKaggle/` directory (see Data Setup section)
- `.env` file created with your local MySQL credentials (see Data Setup section)

**Important**: Make sure you're in the virtual environment and in the `generate_load_data/` directory when running the scripts.

### Loading Steps

**Step 1: Load Artists and Genres**
```bash
cd generate_load_data
python load_artists.py
```
This script:
- Reads `data/SpotifyKaggle/artists.csv`
- Inserts artists into the `Artists` table
- Extracts and normalizes genres into `Genres` table
- Creates `ArtistGenres` junction table entries
- Expected runtime: ~5-10 minutes for ~1.1M artists

**Step 2: Load Tracks**
```bash
python load_tracks.py
```
This script:
- Reads `data/SpotifyKaggle/tracks.csv`
- Normalizes musical attributes to [0,1] range:
  - `loudness`: normalized from dB range (-60 to 0)
  - `tempo`: normalized from BPM range (60-200)
  - `time_signature`: normalized from range (3-7)
  - `key`: normalized from 0-11 to [0,1]
- Inserts tracks into `Tracks` table
- Creates `TrackArtists` junction table entries
- Expected runtime: ~10-15 minutes for ~586K tracks

**Step 3: Generate Fake User Data**
```bash
python generate_fake_users.py [num_users]
```
This script:
- Generates synthetic users, preferences, subscriptions, comments, and likes
- Default: 1000 users (specify custom number as argument)
- Writes CSV files to `processed/` directory:
  - `users.csv` (includes subscription_id, subscription_start_date, subscription_end_date)
  - `preferences.csv`
  - `subscriptions.csv`
  - `comments.csv`
  - `track_likes.csv`
- Expected runtime: ~1-2 minutes for 1000 users

**Step 4: Load Fake User Data**
```bash
python load_fake_users.py
```
This script:
- Reads CSV files from `processed/` directory
- Inserts data in correct order to respect foreign key constraints:
  1. Subscriptions
  2. Users (includes subscription information)
  3. Preferences
  4. Comments
  5. TrackLikes
- Expected runtime: ~2-5 minutes for 1000 users

### Complete Loading Sequence
```bash
cd generate_load_data
python load_artists.py
python load_tracks.py
python generate_fake_users.py 1000
python load_fake_users.py
```

### Verifying Data Load
After loading, verify the data. You can use either method:

**Option A: Python script**
```bash
python test_connection.py
```

**Option B: MySQL CLI**
```bash
mysql -u root -p spotify_db  # or your credentials

-- Check counts
SELECT COUNT(*) FROM Artists;      -- Should be ~1,104,349
SELECT COUNT(*) FROM Genres;        -- Should be ~5,365
SELECT COUNT(*) FROM ArtistGenres; -- Should be ~460,843
SELECT COUNT(*) FROM Tracks;        -- Should be ~586,672
SELECT COUNT(*) FROM TrackArtists; -- Should be ~730,141
SELECT COUNT(*) FROM Users;        -- Depends on num_users you generated
SELECT COUNT(*) FROM TrackLikes;   -- Depends on num_users
SELECT COUNT(*) FROM Comments;     -- Depends on num_users
```

**Expected Results:**
- Artists: ~1,104,349
- Genres: ~5,365 (unique genres)
- ArtistGenres: ~460,843 (artist-genre relationships)
- Tracks: ~586,672
- TrackArtists: ~730,141 (track-artist relationships)

## 6. Troubleshooting

### Common Issues

**Issue: "Unknown database 'spotify_db'"**
- Solution: Make sure you've run the schema setup (Step 6 in Preliminary Project Steps)

**Issue: "ModuleNotFoundError: No module named 'mysql'"**
- Solution: Make sure virtual environment is activated and dependencies are installed

**Issue: "Data too long for column"**
- Solution: The scripts automatically truncate long names/titles. If you see this error, it means the script needs an update.

**Issue: Tracks loading stops before completion**
- Solution: Clear tracks and reload: `TRUNCATE TABLE Tracks; TRUNCATE TABLE TrackArtists;` then rerun `load_tracks.py`

**Issue: MySQL CLI not found**
- Solution: Use the Python alternative: `python setup_db.py` instead of `mysql -u root -p < schema/schema.sql`

## 7. Notes

- **Data Normalization**: Musical attributes are normalized to [0,1] range for similarity calculations
- **Foreign Key Constraints**: Load scripts handle missing references gracefully (skip invalid entries)
- **Batch Processing**: Large datasets are processed in batches to manage memory
- **Duplicate Handling**: Scripts skip duplicate entries automatically
- **Error Handling**: Scripts include error handling and rollback on failures
- **Genre Counts**: The `Genres` table contains unique genre names (~5,365). The `ArtistGenres` table contains the many-to-many relationships (~460,843), which is why that number is much higher.