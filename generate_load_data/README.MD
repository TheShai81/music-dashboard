# Data Processing & Loading (generate_load_data)

This directory contains all scripts used to **transform raw Kaggle data**  
(`artists.csv`, `tracks.csv`) and **load it into the MySQL database** defined in `schema/schema.sql`.

These scripts populate:
- **Artists**
- **Genres + ArtistGenres**
- **Tracks + TrackArtists**
- **Synthetic Users**
- **Friendships / Likes / Comments**
- (Optional) Subscriptions & Preferences

---

## 1. Requirements

Before running these scripts, make sure:

1. The database is initialized:

   ```bash
   mysql -u root -p < schema/schema.sql