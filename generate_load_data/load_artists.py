import csv
import ast
import mysql.connector
from db_config import get_connection

# Load Artists
def load_artists(cur, conn):
    """Load artists from CSV and populate Artists, Genres, and ArtistGenres tables."""
    print("Loading artists from artists.csv...")

    # First pass: collect all unique genres
    genre_set = set()
    artist_data = []

    with open("../data/SpotifyKaggle/artists.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist_id = row["id"]
            name = row["name"]
            followers = int(float(row["followers"])) if row["followers"] else 0
            popularity = int(row["popularity"]) if row["popularity"] else 0

            # Parse genres (format: ['genre1', 'genre2'] or [])
            genres_str = row["genres"]
            try:
                genres_list = ast.literal_eval(genres_str) if genres_str else []
            except (ValueError, SyntaxError):
                genres_list = []

            # Collect genres
            for genre in genres_list:
                if genre and genre.strip():
                    genre_set.add(genre.strip())

            artist_data.append({
                "artist_id": artist_id,
                "name": name,
                "followers": followers,
                "popularity": popularity,
                "genres": genres_list
            })

    print(f"Found {len(genre_set)} unique genres")
    print(f"Found {len(artist_data)} artists")

    # Insert genres
    print("Inserting genres...")
    genre_map = {}  # genre_name -> genre_id
    insert_genre_sql = "INSERT INTO Genres (genre_name) VALUES (%s)"

    for genre in sorted(genre_set):
        cur.execute(insert_genre_sql, (genre,))
        genre_id = cur.lastrowid
        genre_map[genre] = genre_id

    conn.commit()
    print(f"Inserted {len(genre_map)} genres")

    # Insert artists
    print("Inserting artists...")
    insert_artist_sql = """
        INSERT INTO Artists (artist_id, name, followers, popularity)
        VALUES (%s, %s, %s, %s)
    """

    batch_size = 1000
    for i in range(0, len(artist_data), batch_size):
        batch = artist_data[i:i + batch_size]
        for artist in batch:
            try:
                # Truncate name to fit VARCHAR(200) if needed
                name = artist["name"][:200] if len(artist["name"]) > 200 else artist["name"]
                cur.execute(insert_artist_sql, (
                    artist["artist_id"],
                    name,
                    artist["followers"],
                    artist["popularity"]
                ))
            except mysql.connector.IntegrityError as e:
                # Skip duplicates
                print(f"Warning: Skipping duplicate artist {artist['artist_id']}: {e}")
                continue

        conn.commit()
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Inserted {min(i + batch_size, len(artist_data))} / {len(artist_data)} artists")

    print(f"Inserted {len(artist_data)} artists")

    # Insert ArtistGenres junction table
    print("Inserting artist-genre relationships...")
    insert_ag_sql = """
        INSERT INTO ArtistGenres (artist_id, genre_id)
        VALUES (%s, %s)
    """

    ag_count = 0
    for artist in artist_data:
        for genre in artist["genres"]:
            if genre and genre.strip() and genre.strip() in genre_map:
                try:
                    cur.execute(insert_ag_sql, (
                        artist["artist_id"],
                        genre_map[genre.strip()]
                    ))
                    ag_count += 1
                except mysql.connector.IntegrityError:
                    # Skip duplicates
                    pass

        if ag_count % 10000 == 0 and ag_count > 0:
            conn.commit()
            print(f"  Inserted {ag_count} artist-genre relationships...")

    conn.commit()
    print(f"Inserted {ag_count} artist-genre relationships")


if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()

    try:
        load_artists(cur, conn)
        print("Artists loading completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

