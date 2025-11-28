-- Create database and app user
CREATE DATABASE IF NOT EXISTS spotify_db
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'spotify_user'@'%'
  IDENTIFIED BY 'Spotify123!';

GRANT ALL PRIVILEGES ON spotify_db.* TO 'spotify_user'@'%';
FLUSH PRIVILEGES;

USE spotify_db;

-- =====================
-- Subscriptions
-- =====================

CREATE TABLE Subscriptions (
    sub_id        INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(50) NOT NULL UNIQUE,
    cost          DECIMAL(6,2) NOT NULL,
    max_playlists INT NOT NULL
);

-- =====================
-- Core user-related
-- =====================

CREATE TABLE Users (
    user_id        INT AUTO_INCREMENT PRIMARY KEY,
    username       VARCHAR(50) NOT NULL UNIQUE,
    email          VARCHAR(100) NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subscription_id INT,
    subscription_start_date DATE,
    subscription_end_date DATE,
    CONSTRAINT fk_user_subscription FOREIGN KEY (subscription_id)
        REFERENCES Subscriptions(sub_id)
        ON DELETE SET NULL
);

CREATE TABLE Friendships (
    user_id1        INT NOT NULL,
    user_id2        INT NOT NULL,
    date_befriended DATE NOT NULL,
    PRIMARY KEY (user_id1, user_id2),
    CONSTRAINT fk_friends_u1 FOREIGN KEY (user_id1)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_friends_u2 FOREIGN KEY (user_id2)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,
    -- ensure user_id1 < user_id2 to avoid duplicates in app logic
    CHECK (user_id1 <> user_id2)
);

CREATE TABLE Preferences (
    user_id    INT PRIMARY KEY,
    theme      VARCHAR(20) DEFAULT 'light',
    pfp_color  VARCHAR(20),
    CONSTRAINT fk_prefs_user FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
        ON DELETE CASCADE
);

-- =====================
-- Artists / Genres
-- =====================

CREATE TABLE Artists (
    artist_id   VARCHAR(32) PRIMARY KEY,  -- Spotify ID from artists.csv
    name        VARCHAR(200) NOT NULL,
    followers   INT,
    popularity  INT
);

CREATE TABLE Genres (
    genre_id    INT AUTO_INCREMENT PRIMARY KEY,
    genre_name  VARCHAR(100) NOT NULL UNIQUE
);

-- M:N Artists <-> Genres
CREATE TABLE ArtistGenres (
    artist_id  VARCHAR(32) NOT NULL,
    genre_id   INT NOT NULL,
    PRIMARY KEY (artist_id, genre_id),
    CONSTRAINT fk_ag_artist FOREIGN KEY (artist_id)
        REFERENCES Artists(artist_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ag_genre FOREIGN KEY (genre_id)
        REFERENCES Genres(genre_id)
        ON DELETE CASCADE
);

-- =====================
-- Tracks and musical attributes
-- =====================

CREATE TABLE Tracks (
    track_id       VARCHAR(32) PRIMARY KEY,  -- Spotify ID from tracks.csv
    title          VARCHAR(300) NOT NULL,
    release_date   DATE,
    duration_ms    INT,
    explicit       BOOLEAN,
    key_signature  TINYINT,   -- 0-11 from Spotify "key"
    mode           TINYINT,   -- 0=min, 1=maj
    danceability   FLOAT,
    energy         FLOAT,
    loudness       FLOAT,
    speechiness    FLOAT,
    acousticness   FLOAT,
    instrumentalness FLOAT,
    liveness       FLOAT,
    valence        FLOAT,
    tempo          FLOAT,
    time_signature TINYINT,
    popularity     INT
);

-- M:N Tracks <-> Artists (from id_artists list)
CREATE TABLE TrackArtists (
    track_id   VARCHAR(32) NOT NULL,
    artist_id  VARCHAR(32) NOT NULL,
    PRIMARY KEY (track_id, artist_id),
    CONSTRAINT fk_ta_track FOREIGN KEY (track_id)
        REFERENCES Tracks(track_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_ta_artist FOREIGN KEY (artist_id)
        REFERENCES Artists(artist_id)
        ON DELETE CASCADE
);

-- =====================
-- Comments and Likes
-- =====================

CREATE TABLE Comments (
    comment_id  INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    track_id    VARCHAR(32) NOT NULL,
    content     TEXT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_comments_user FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_comments_track FOREIGN KEY (track_id)
        REFERENCES Tracks(track_id)
        ON DELETE CASCADE
);

CREATE TABLE TrackLikes (
    user_id   INT NOT NULL,
    track_id  VARCHAR(32) NOT NULL,
    liked_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, track_id),
    CONSTRAINT fk_likes_user FOREIGN KEY (user_id)
        REFERENCES Users(user_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_likes_track FOREIGN KEY (track_id)
        REFERENCES Tracks(track_id)
        ON DELETE CASCADE
);

-- Helpful indexes for queries
CREATE INDEX idx_tracks_popularity ON Tracks(popularity);
CREATE INDEX idx_tracks_release ON Tracks(release_date);
CREATE INDEX idx_comments_track ON Comments(track_id);
CREATE INDEX idx_likes_track ON TrackLikes(track_id);
