import csv
import ast
import mysql.connector
from datetime import datetime
from db_config import get_connection


def normalize_loudness(loudness):
    """Normalize loudness from dB range (-60 to 0) to [0, 1]."""
    if loudness is None or loudness == "":
        return None
    # Clamp to reasonable range and normalize
    loudness = float(loudness)
    # Typical range is -60 to 0 dB
    normalized = (loudness + 60) / 60.0
    return max(0.0, min(1.0, normalized))


def normalize_tempo(tempo):
    """Normalize tempo from BPM range (typically 60-200) to [0, 1]."""
    if tempo is None or tempo == "":
        return None
    tempo = float(tempo)
    # Clamp to reasonable range and normalize
    # Using 60-200 BPM as typical range
    normalized = (tempo - 60) / 140.0
    return max(0.0, min(1.0, normalized))


def normalize_time_signature(ts):
    """Normalize time signature (typically 3-7) to [0, 1]."""
    if ts is None or ts == "":
        return None
    ts = int(float(ts))
    # Clamp to reasonable range and normalize
    normalized = (ts - 3) / 4.0  # 3-7 range
    return max(0.0, min(1.0, normalized))


def parse_release_date(date_str):
    """Parse release date from various formats (YYYY-MM-DD, YYYY-MM, YYYY) to DATE."""
    if not date_str or date_str == "":
        return None

    date_str = date_str.strip()

    # Try different formats
    formats = ["%Y-%m-%d", "%Y-%m", "%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None


def normalize_key(key):
    """Normalize key (0-11) to [0, 1] using dummy encoding approach."""
    if key is None or key == "":
        return None
    key = int(float(key))
    # Simple normalization: divide by 11
    return key / 11.0


# Load Tracks
def load_tracks(cur, conn):
    """Load tracks from CSV and populate Tracks and TrackArtists tables."""
    print("Loading tracks from tracks.csv...")

    track_data = []
    track_artists_data = []

    with open("../data/SpotifyKaggle/tracks.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            track_id = row["id"]
            title = row["name"]
            popularity = int(row["popularity"]) if row["popularity"] else 0
            duration_ms = int(float(row["duration_ms"])) if row["duration_ms"] else None
            explicit = bool(int(row["explicit"])) if row["explicit"] else False
            release_date = parse_release_date(row["release_date"])

            # Parse id_artists (format: ['id1', 'id2'])
            id_artists_str = row["id_artists"]
            try:
                id_artists_list = ast.literal_eval(id_artists_str) if id_artists_str else []
            except (ValueError, SyntaxError):
                id_artists_list = []

            # Normalize musical attributes to [0, 1]
            danceability = float(row["danceability"]) if row["danceability"] else None
            energy = float(row["energy"]) if row["energy"] else None
            key_normalized = normalize_key(row["key"])
            loudness_normalized = normalize_loudness(row["loudness"])
            mode = int(float(row["mode"])) if row["mode"] else None
            speechiness = float(row["speechiness"]) if row["speechiness"] else None
            acousticness = float(row["acousticness"]) if row["acousticness"] else None
            instrumentalness = float(row["instrumentalness"]) if row["instrumentalness"] else None
            liveness = float(row["liveness"]) if row["liveness"] else None
            valence = float(row["valence"]) if row["valence"] else None
            tempo_normalized = normalize_tempo(row["tempo"])
            time_signature_normalized = normalize_time_signature(row["time_signature"])

            # Keep original key for key_signature column (0-11)
            key_signature = int(float(row["key"])) if row["key"] else None

            # Truncate title to fit VARCHAR(300) if needed
            title_truncated = title[:300] if len(title) > 300 else title

            track_data.append({
                "track_id": track_id,
                "title": title_truncated,
                "release_date": release_date,
                "duration_ms": duration_ms,
                "explicit": explicit,
                "key_signature": key_signature,
                "mode": mode,
                "danceability": danceability,
                "energy": energy,
                "loudness": loudness_normalized,
                "speechiness": speechiness,
                "acousticness": acousticness,
                "instrumentalness": instrumentalness,
                "liveness": liveness,
                "valence": valence,
                "tempo": tempo_normalized,
                "time_signature": time_signature_normalized,
                "popularity": popularity
            })

            # Store track-artist relationships
            for artist_id in id_artists_list:
                if artist_id and artist_id.strip():
                    track_artists_data.append({
                        "track_id": track_id,
                        "artist_id": artist_id.strip()
                    })

    print(f"Found {len(track_data)} tracks")
    print(f"Found {len(track_artists_data)} track-artist relationships")

    # Insert tracks
    print("Inserting tracks...")
    insert_track_sql = """
        INSERT INTO Tracks (
            track_id, title, release_date, duration_ms, explicit,
            key_signature, mode, danceability, energy, loudness,
            speechiness, acousticness, instrumentalness, liveness,
            valence, tempo, time_signature, popularity
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )
    """

    batch_size = 1000
    inserted_count = 0
    for i in range(0, len(track_data), batch_size):
        batch = track_data[i:i + batch_size]
        for track in batch:
            try:
                cur.execute(insert_track_sql, (
                    track["track_id"],
                    track["title"],
                    track["release_date"],
                    track["duration_ms"],
                    track["explicit"],
                    track["key_signature"],
                    track["mode"],
                    track["danceability"],
                    track["energy"],
                    track["loudness"],
                    track["speechiness"],
                    track["acousticness"],
                    track["instrumentalness"],
                    track["liveness"],
                    track["valence"],
                    track["tempo"],
                    track["time_signature"],
                    track["popularity"]
                ))
                inserted_count += 1
            except mysql.connector.IntegrityError as e:
                # Skip duplicates
                print(f"Warning: Skipping duplicate track {track['track_id']}: {e}")
                continue

        conn.commit()
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Inserted {min(i + batch_size, len(track_data))} / {len(track_data)} tracks")

    print(f"Inserted {inserted_count} tracks")

    # Insert TrackArtists junction table
    print("Inserting track-artist relationships...")
    insert_ta_sql = """
        INSERT INTO TrackArtists (track_id, artist_id)
        VALUES (%s, %s)
    """

    ta_count = 0
    batch_size = 5000
    for i in range(0, len(track_artists_data), batch_size):
        batch = track_artists_data[i:i + batch_size]
        for ta in batch:
            try:
                cur.execute(insert_ta_sql, (ta["track_id"], ta["artist_id"]))
                ta_count += 1
            except mysql.connector.IntegrityError:
                # Skip duplicates or invalid foreign keys
                pass
            except mysql.connector.Error as e:
                # Skip if artist doesn't exist
                pass

        conn.commit()
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Inserted {ta_count} track-artist relationships...")

    print(f"Inserted {ta_count} track-artist relationships")


if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()

    try:
        load_tracks(cur, conn)
        print("Tracks loading completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

