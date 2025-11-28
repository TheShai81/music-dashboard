import csv
import random
import hashlib
from datetime import datetime, timedelta
import os


def generate_password_hash(password):
    """Generate a simple password hash (for demo purposes)."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_fake_users(num_users=1000):
    """Generate fake users, preferences, subscriptions, and engagement data."""
    print(f"Generating {num_users} fake users...")

    # Create processed directory if it doesn't exist
    os.makedirs("../processed", exist_ok=True)

    # Subscription tiers
    subscriptions = [
        {"name": "Free", "cost": 0.00, "max_playlists": 15},
        {"name": "Premium Individual", "cost": 9.99, "max_playlists": 10000},
        {"name": "Premium Family", "cost": 14.99, "max_playlists": 10000},
        {"name": "Premium Student", "cost": 4.99, "max_playlists": 10000},
    ]

    # Themes and colors
    themes = ["light", "dark", "auto"]
    colors = ["#1DB954", "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", "#F7DC6F", "#BB8FCE"]

    # Generate users
    users = []
    preferences = []

    for i in range(1, num_users + 1):
        username = f"user_{i:06d}"
        email = f"{username}@example.com"
        password = f"password{i}"
        password_hash = generate_password_hash(password)
        created_at = datetime.now() - timedelta(days=random.randint(0, 365))

        # Subscription info (stored directly in Users table)
        subscription_id = None
        subscription_start_date = None
        subscription_end_date = None

        if random.random() < 0.85:  # 85% have subscriptions
            sub = random.choice(subscriptions)
            subscription_id = subscriptions.index(sub) + 1
            subscription_start_date = (created_at.date() + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d")
            # Some subscriptions are active, some expired
            if random.random() < 0.7:  # 70% active
                subscription_end_date = None
            else:
                subscription_end_date = (datetime.strptime(subscription_start_date, "%Y-%m-%d").date() + timedelta(days=random.randint(30, 365))).strftime("%Y-%m-%d")

        users.append({
            "user_id": i,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "subscription_id": subscription_id,
            "subscription_start_date": subscription_start_date,
            "subscription_end_date": subscription_end_date
        })

        # Preferences
        preferences.append({
            "user_id": i,
            "theme": random.choice(themes),
            "pfp_color": random.choice(colors)
        })

    # Write users CSV
    print("Writing users.csv...")
    with open("../processed/users.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "username", "email", "password_hash", "created_at", "subscription_id", "subscription_start_date", "subscription_end_date"])
        writer.writeheader()
        writer.writerows(users)

    # Write preferences CSV
    print("Writing preferences.csv...")
    with open("../processed/preferences.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "theme", "pfp_color"])
        writer.writeheader()
        writer.writerows(preferences)

    # Write subscriptions CSV
    print("Writing subscriptions.csv...")
    with open("../processed/subscriptions.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sub_id", "name", "cost", "max_playlists"])
        writer.writeheader()
        for i, sub in enumerate(subscriptions, 1):
            writer.writerow({
                "sub_id": i,
                "name": sub["name"],
                "cost": sub["cost"],
                "max_playlists": sub["max_playlists"]
            })

    print(f"Generated {len(users)} users, {len(preferences)} preferences")

    return len(users)


def generate_comments_and_likes(num_users, num_comments_per_user=5, num_likes_per_user=20):
    """Generate comments and likes. Requires tracks to exist in database."""
    print("Generating comments and likes...")
    print("Note: This requires tracks to be loaded first. We'll generate track IDs from the CSV.")

    # Get track IDs from tracks.csv
    track_ids = []
    try:
        with open("../data/SpotifyKaggle/tracks.csv", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                track_ids.append(row["id"])
    except FileNotFoundError:
        print("Warning: tracks.csv not found. Skipping comments and likes generation.")
        return

    if not track_ids:
        print("Warning: No tracks found. Skipping comments and likes generation.")
        return

    print(f"Found {len(track_ids)} tracks")

    # Sample comments
    comment_templates = [
        "Love this song!",
        "This is my favorite track.",
        "Great vibes!",
        "Perfect for studying.",
        "Can't stop listening to this.",
        "Amazing artist!",
        "This song hits different.",
        "Added to my playlist!",
        "So good!",
        "Classic!",
        "Underrated gem.",
        "Perfect workout song.",
        "This brings back memories.",
        "Incredible production!",
        "One of the best tracks ever.",
    ]

    comments = []
    track_likes = []

    for user_id in range(1, num_users + 1):
        # Generate comments
        num_comments = random.randint(0, num_comments_per_user)
        commented_tracks = random.sample(track_ids, min(num_comments, len(track_ids)))

        for track_id in commented_tracks:
            comment_text = random.choice(comment_templates)
            created_at = datetime.now() - timedelta(
                days=random.randint(0, 180),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            comments.append({
                "user_id": user_id,
                "track_id": track_id,
                "content": comment_text,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # Generate likes
        num_likes = random.randint(5, num_likes_per_user)
        liked_tracks = random.sample(track_ids, min(num_likes, len(track_ids)))

        for track_id in liked_tracks:
            liked_at = datetime.now() - timedelta(
                days=random.randint(0, 365),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )

            track_likes.append({
                "user_id": user_id,
                "track_id": track_id,
                "liked_at": liked_at.strftime("%Y-%m-%d %H:%M:%S")
            })

    # Write comments CSV
    print("Writing comments.csv...")
    with open("../processed/comments.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "track_id", "content", "created_at"])
        writer.writeheader()
        writer.writerows(comments)

    # Write track_likes CSV
    print("Writing track_likes.csv...")
    with open("../processed/track_likes.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["user_id", "track_id", "liked_at"])
        writer.writeheader()
        writer.writerows(track_likes)

    print(f"Generated {len(comments)} comments and {len(track_likes)} likes")


if __name__ == "__main__":
    import sys

    num_users = 1000
    if len(sys.argv) > 1:
        num_users = int(sys.argv[1])

    num_users_created = generate_fake_users(num_users)
    generate_comments_and_likes(num_users_created)

    print("\nFake user data generation completed!")
    print(f"CSV files written to ../processed/ directory")

