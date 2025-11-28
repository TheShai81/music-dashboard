# Data Folder

This project uses the Kaggle "Spotify Datasets" (artists + tracks).

## Download Instructions

1. **Download from Kaggle**: https://www.kaggle.com/datasets/lehaknarnauli/spotify-datasets
2. **Create the subdirectory**:
   ```bash
   mkdir -p SpotifyKaggle
   ```
3. **Place the following files** into `SpotifyKaggle/`:
   - `artists.csv` (~1.1M rows)
   - `tracks.csv` (~586K rows)

Your directory structure should look like:
```
data/
  SpotifyKaggle/
    artists.csv
    tracks.csv
```

## Important Notes

- These files are **intentionally NOT committed** to git because of their large size
- Each team member must download the files locally
- The `.gitignore` file excludes `data/SpotifyKaggle/` and all `.csv` files
- See the main `README.md` for complete setup instructions