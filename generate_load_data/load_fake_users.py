import csv
import mysql.connector
from db_config import get_connection


def load_subscriptions(cur, conn):
    """Load subscriptions from CSV."""
    print("Loading subscriptions...")
    insert_sql = "INSERT INTO Subscriptions (sub_id, name, cost, max_playlists) VALUES (%s, %s, %s, %s)"

    with open("../processed/subscriptions.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cur.execute(insert_sql, (
                    int(row["sub_id"]),
                    row["name"],
                    float(row["cost"]),
                    int(row["max_playlists"])
                ))
            except mysql.connector.IntegrityError:
                # Skip duplicates
                pass

    conn.commit()
    print("Subscriptions loaded")


def load_users(cur, conn):
    """Load users from CSV."""
    print("Loading users...")
    insert_sql = """
        INSERT INTO Users (user_id, username, email, password_hash, created_at,
                          subscription_id, subscription_start_date, subscription_end_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    batch_size = 1000
    count = 0

    with open("../processed/users.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batch = []
        for row in reader:
            batch.append((
                int(row["user_id"]),
                row["username"],
                row["email"],
                row["password_hash"],
                row["created_at"],
                int(row["subscription_id"]) if row["subscription_id"] else None,
                row["subscription_start_date"] if row["subscription_start_date"] else None,
                row["subscription_end_date"] if row["subscription_end_date"] else None
            ))

            if len(batch) >= batch_size:
                for data in batch:
                    try:
                        cur.execute(insert_sql, data)
                        count += 1
                    except mysql.connector.IntegrityError:
                        pass
                conn.commit()
                batch = []
                print(f"  Loaded {count} users...")

        # Process remaining
        for data in batch:
            try:
                cur.execute(insert_sql, data)
                count += 1
            except mysql.connector.IntegrityError:
                pass
        conn.commit()

    print(f"Loaded {count} users")


def load_preferences(cur, conn):
    """Load preferences from CSV."""
    print("Loading preferences...")
    insert_sql = "INSERT INTO Preferences (user_id, theme, pfp_color) VALUES (%s, %s, %s)"

    count = 0
    with open("../processed/preferences.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                cur.execute(insert_sql, (
                    int(row["user_id"]),
                    row["theme"],
                    row["pfp_color"]
                ))
                count += 1
            except mysql.connector.IntegrityError:
                pass

    conn.commit()
    print(f"Loaded {count} preferences")


def load_comments(cur, conn):
    """Load comments from CSV."""
    print("Loading comments...")
    insert_sql = """
        INSERT INTO Comments (user_id, track_id, content, created_at)
        VALUES (%s, %s, %s, %s)
    """

    batch_size = 5000
    count = 0
    batch = []

    with open("../processed/comments.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append((
                int(row["user_id"]),
                row["track_id"],
                row["content"],
                row["created_at"]
            ))

            if len(batch) >= batch_size:
                for data in batch:
                    try:
                        cur.execute(insert_sql, data)
                        count += 1
                    except mysql.connector.IntegrityError:
                        pass
                    except mysql.connector.Error:
                        # Skip if track doesn't exist
                        pass
                conn.commit()
                batch = []
                if count % 10000 == 0:
                    print(f"  Loaded {count} comments...")

        # Process remaining
        for data in batch:
            try:
                cur.execute(insert_sql, data)
                count += 1
            except mysql.connector.IntegrityError:
                pass
            except mysql.connector.Error:
                pass
        conn.commit()

    print(f"Loaded {count} comments")


def load_track_likes(cur, conn):
    """Load track likes from CSV."""
    print("Loading track likes...")
    insert_sql = """
        INSERT INTO TrackLikes (user_id, track_id, liked_at)
        VALUES (%s, %s, %s)
    """

    batch_size = 10000
    count = 0
    batch = []

    with open("../processed/track_likes.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append((
                int(row["user_id"]),
                row["track_id"],
                row["liked_at"]
            ))

            if len(batch) >= batch_size:
                for data in batch:
                    try:
                        cur.execute(insert_sql, data)
                        count += 1
                    except mysql.connector.IntegrityError:
                        # Skip duplicates
                        pass
                    except mysql.connector.Error:
                        # Skip if track doesn't exist
                        pass
                conn.commit()
                batch = []
                if count % 50000 == 0:
                    print(f"  Loaded {count} likes...")

        # Process remaining
        for data in batch:
            try:
                cur.execute(insert_sql, data)
                count += 1
            except mysql.connector.IntegrityError:
                pass
            except mysql.connector.Error:
                pass
        conn.commit()

    print(f"Loaded {count} track likes")


if __name__ == "__main__":
    conn = get_connection()
    cur = conn.cursor()

    try:
        # Load in order to respect foreign key constraints
        load_subscriptions(cur, conn)
        load_users(cur, conn)
        load_preferences(cur, conn)
        load_comments(cur, conn)
        load_track_likes(cur, conn)

        print("\nFake user data loading completed successfully!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

