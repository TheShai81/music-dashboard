from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app, abort
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import date
import numpy as np
from numpy.linalg import norm
import random

bp = Blueprint('main', __name__, template_folder="templates")

@bp.route('/register', methods=['GET', 'POST'])
def register():
    '''
    If a "register" redirect is sent to the server, this function emits a render template signal
    redirecting to "register.html".

    Registers a new user into the app from the register html page if a POST is received.
    Expects the following data from a frontend POST:
        - username (str): the username they chose
        - email (str): the email they chose
        - password (str): the password they chose. hashed later.
        - theme (str): the user preference for light or dark mode. aka the theme of the app
        - pfp_color (str): the color they want their profile picture to be

    If POST successful, redirects to login page. If unsuccessful, returns FAILED. If no POST, just renders
    register.html.
    '''
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        theme = request.form['theme']
        pfp_color = request.form['pfp_color']

        try:
            cursor = current_app.db.cursor(dictionary=True)
            # user info insertion
            created_at = date.today().strftime("%Y-%m-%d")
            query = "INSERT INTO Users (username, email, password_hash, created_at) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (username, email, hashed_pw, created_at))
            current_app.db.commit()
            
            # preferences insertion
            user_id = cursor.lastrowid
            query_pref = "INSERT INTO Preferences (user_id, theme, pfp_color) VALUES (%s, %s, %s)"
            cursor.execute(query_pref, (user_id, theme, pfp_color))
            current_app.db.commit()
            cursor.close()

            return redirect(url_for('main.login'))
        except Exception as e:
            print(e)
            return "Failed"
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    '''
    Renders the login template upon redirect to login.html.

    Upon POST, checks if user exists and their password is correct. If both are successful, then redirects to the main
    user page home.html. Else, returns the string "Login failed."
    If there are multiple users with the same username, this just selects the first one in the table.

    Information expected from login.html POST:
        - username_or_email (str): the username or the email of the user
        - password (str): the submitted, unhashed password
    '''
    if request.method == 'POST':
        cursor = current_app.db.cursor(dictionary=True)

        username_or_email = request.form['username_or_email']
        password = request.form['password']
        query = "SELECT * FROM Users WHERE username=%s OR email=%s"
        cursor.execute(query, (username_or_email, username_or_email))
        user = cursor.fetchone()
        cursor.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            return redirect(url_for('main.home'))
        else:
            return "Login failed."
    return render_template('login.html')


@bp.route('/home')
def home():
    '''
    A user's home page that shows them their own information.

    This always returns a list of liked songs (which are tuples in the list I think) and a list of friends.
    Upon receiving a POST from the page (such as one for computing friend compatibility or whatever), the appropriate
    queries will be run and returned (data attribute names tbd).

    Information expected from POST:
        - desired_query (str): data of the type input (i.e. a radio button) that describes the query we should run
        in the backend. The names of some queries that this expects are below:
            - dashboard: the user dashboard of their listening insights
            - soulmate: find musical soulmate or the most compatible friend
            - compatibility: calculate compatibility with a certain friend
                - Requires `friend_id` attr. The friend with whom to calculate compatibility
            - genres: top 3 most liked to genres
            - artists: top 3 most liked artists
            - obscurity: how obscure is their music taste
            - music_age: how "old" is their music
            - discovery: generate a discovery playlist for the user
            - recommend_friend: recommend a friend of a friend based on similarity
                - Requires `friend_id` attr. The friend of whom to find a friend

    For full information on what each of the above possible desired queries sends to the frontend, read each query's
    function's docstring for clear return value descriptions with field names and data types.

    Information returned to frontend under the accessible variable name `query_results`.
    '''
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    liked_songs = []
    friends = []
    
    # find liked songs
    query = "SELECT t.track_id, t.title, t.duration_ms, t.release_date FROM Tracks t JOIN TrackLikes tl ON t.track_id = tl.track_id WHERE tl.user_id = %s"
    cursor = current_app.db.cursor(dictionary=True)
    cursor.execute(query, (user_id))
    liked_songs = cursor.fetchall()
    # find friends
    query = "SELECT u.user_id, u.username, f.date_befriended FROM Users u " \
            "JOIN Friendships f ON" \
            "(u.user_id = f.user_id1 AND f.user_id2 = %s) OR (u.user_id = f.user_id2 AND f.user_id1 = %s)"
    cursor.execute(query, (user_id))
    friends = cursor.fetchall()
    cursor.close()

    query_results = []
    if request.method == 'POST':
        desired_query = request.form['desired_query']
        match desired_query:
            case "artists":
                query_results = top_3_artists()
            case "genres":
                query_results = top_3_genres()
            case "discovery":
                query_results = create_discovery_playlist()
            case "soulmate":
                query_results = find_soulmate()
            case "compatibility":
                # expects the id of the friend to calculate compatibility with to be passed in POST
                friend = request.form['friend_id']
                query_results = round(get_compatibility(friend), 1)  # round to 1 decimal place
            case "recommend_friend":
                query_results = recommend_friend()
            case "dashboard":
                query_results = create_dashboard()
            case "obscurity":
                query_results = calculate_obscurity()
            case "music_age":
                query_results = calculate_music_age()
            case _:
                abort(404)

    dashboard_data = {
        'liked_songs': [], 
        'top_genres': [],
        'friend_recommendations': []
    }

    return render_template('home.html',
                           liked_songs=liked_songs,
                           friends=friends,
                           query_results=query_results)


@bp.route('/search', methods=['GET', 'POST'])
def search():
    '''
    Searches across Users, Artists, and Tracks to find a match to the submitted string.

    Information expected from POST:
        - user_keyword (str): the keyword if this is a user search
        - track_keyword (str): the keyword if this is a track search
        - artist_keyword (str): the keyword if this is an artist search
    
    Note: User searches must be mutually exclusive with track/artist searches, but track/artist\
    searches can happen simultaneously.
    i.e. There should be three input boxes in the front end: one for user search, one for track, and one for artist.\
    However, track and artist are submitted simultaneously even if one or the other is empty.
    
    Sends the following data to frontend:

        users = [
            {
                'user_id': int,
                'username': str,
                'friend': bool 1/0
            }
        ]

        artists = [
            'artist_id': int, 
            'name': str, 
            'popularity': int]
        ]

        tracks = [
            {
                'track_id': int, 
                'title': str, 
                'artist_name': str, 
                'duration': int (seconds)
            }
        ]
    '''

    users = []
    tracks = []
    artists = []

    if request.method == 'POST':
        user_keyword = request.form['user_keyword']
        track_keyword = request.form['track_keyword']
        artist_keyword = request.form['artist_keyword']
        results = {}
        if user_keyword and user_keyword != "":
            users = search_users(user_keyword)
            tracks = []
            artists = []
        elif track_keyword and track_keyword != "":
            tracks = search_tracks(track_keyword, artist_keyword if artist_keyword else "")
            users = []
            if artist_keyword and artist_keyword != "":
                artists = search_artists(artist_keyword)
            else:
                artists = []
        elif artist_keyword and artist_keyword != "":
            artists = search_artists(artist_keyword)
            tracks = []
            users = []

    return render_template('search.html',
                           users=users,
                           tracks=tracks,
                           artists=artists)


@bp.route('/artist/<artist_id>')
def artist_page(artist_id):
    '''
    An artist page. Only expects `artist_id` attribute to render template.

    Information sent to frontend:

        artist = {
            name: str,
            popularity: int
        }

        tracks = [
            {
                track_id: int,
                title: str,
                duration: int (in seconds),
                explicit: bool
            }
        ]
    '''

    page_data = artist_page_data(artist_id)

    return render_template('artist.html',
                           artist=page_data["artist_info"],
                           tracks=page_data["tracks"])


@bp.route('/user/<int:user_id>')
def user_page(user_id):
    '''
    A user page. Only expects `user_id` to render template.

    Information sent to frontend:

        user = {
            username: str,
            pfp_color: str
        }

        liked_tracks = [
            {
                track_id: int,
                title: str,
                duration: int (in seconds),
                artists: List[str],
            }
        ]

        friends = [
            {
                friend_id: int,
                friend_name: str
            }
        ]
    '''
    # TODO: implement function to etch user info, liked tracks, and friends
    page_data = user_page_data(user_id)
    user_info = {}
    liked_tracks = []
    friends = []

    return render_template('user.html',
                           user=page_data["user_info"],
                           liked_tracks=page_data["liked_tracks"],
                           friends=page_data["friends"])


@bp.route('/track/<track_id>', methods=['GET', 'POST'])
def track_page(track_id):
    '''
    A track page. Only requires `track_id` to render template.

    Information expected from POST (for commenting and liking the track only):
        - comment (str): the comment a user left. Empty string if no comment and this POST is about a like.
        - liked (bool): if a user liked the track. False if this POST is about a comment. Also True if a user \
        *unliked* a track so that we can toggle this.
        - similar_tracks (bool): True if a user requested to see 10 similar tracks to this one. False otherwise.
    
    Information sent to frontend:

        track = {
            title: str,
            release_date: str,
            duration: int (secs),
            explicit: boolean,
            key_signature: int,
            popularity: int,
            liked: bool (whether user has liked the track)
        }
        
        comments = [
            {
                username: str,
                content: str,
                created_at: str
            }
        ]

        (if requested)
        similar_tracks = [
            {
                track_id: int,
                title: str
            }
        ]
    '''
    
    # variable in case the user has requested 10 songs similar to the current one
    top_10 = []

    user_id = session["user_id"]

    if request.method == 'POST':
        user_id = session["user_id"]
        track_id = request.form["track_id"]
        comment = request.form.get("comment", "").strip()
        liked = request.form.get("liked")
        similar_tracks = request.form.get("similar_tracks")

        cursor = current_app.db.cursor(dictionary=True)

        if comment != "":
            # insert comment from user
            today = date.today().strftime('%Y-%m-%d')
            insert_comment_query = """
                INSERT INTO Comments (user_id, track_id, content, created_at)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_comment_query, (user_id, track_id, comment, today))
            current_app.db.commit()
        if liked:
            # update tracklikes (if the user hasn't liked yet, add it. but if they have liked it, then remove the like)
            check_like_query = """
                SELECT 1
                FROM TrackLikes
                WHERE user_id = %s AND track_id = %s
            """
            cursor.execute(check_like_query, (user_id, track_id))
            already_liked = cursor.fetchone() is not None

            if already_liked:
                # unlike
                unlike_query = """
                    DELETE FROM TrackLikes
                    WHERE user_id = %s AND track_id = %s
                """
                cursor.execute(unlike_query, (user_id, track_id))
            else:
                # add like
                today = date.today().strftime('%Y-%m-%d')
                like_query = """
                    INSERT INTO TrackLikes (user_id, track_id, liked_at)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(like_query, (user_id, track_id, today))
            
            current_app.db.commit()
        if similar_tracks:
            # find 10 similar tracks
            top_10 = get_similar_tracks(track_id)
        
    page_data = track_page_data(track_id)

    return render_template('track.html',
                           track=page_data["track_info"],
                           comments=page_data["comments"],
                           similar_tracks=top_10)

########################################################
# TODO: Implement helper functions for complex queries #
########################################################

def search_users(keyword: str):
    '''
    Searches for users with `keyword` in their name. Limits search results to first 10 results.
    
    :param keyword: Description
    :type keyword: str

    :returns result: List[dict[user_id: int, username: str, friend: bool]] where\
    `friend` is a boolean describing whether the user is friends with the querying user. Up to length 10 and sorts on\
    `friend` from True to False.
    '''

    CURRENT_USER_ID = session['user_id']
    cursor = current_app.db.cursor(dictionary=True)

    query = """
    SELECT 
        u.user_id,
        u.username,
        CASE
            WHEN f.user_id1 IS NOT NULL OR f.user_id2 IS NOT NULL THEN TRUE
            ELSE FALSE
        END AS friend
    FROM Users u
    LEFT JOIN Friendships f
        ON (f.user_id1 = %s AND f.user_id2 = u.user_id)
        OR (f.user_id2 = %s AND f.user_id1 = u.user_id)
    WHERE u.username LIKE %s
      AND u.user_id != %s
    ORDER BY friend DESC, u.username ASC
    LIMIT 10;
    """
    search_term = f"%{keyword}%"

    cursor.execute(query, (CURRENT_USER_ID, CURRENT_USER_ID, search_term, CURRENT_USER_ID))
    result = cursor.fetchall()
    cursor.close()

    return result

def search_tracks(track_keyword: str, artist_keyword: str):
    '''
    Searches for tracks with `track_keyword` and, if not empty, searches for tracks whose artist is `artist_keyword`.
    
    :param track_keyword: the track to be searched
    :type track_keyword: str
    :param artist_keyword: the artist of the track (can be empty)
    :type artist_keyword: str

    :returns result: List[dict[track_id: int, title: str, artist_name: str, duration: int]]. Duration is converted from\
    ms in the database to seconds in the returned variable.
    '''

    cursor = current_app.db.cursour(dictionary=True)
    base_query = """
        SELECT
            t.track_id,
            t.title,
            a.name AS artist_name,
            t.duration_ms
        FROM Tracks t
        JOIN TrackArtists ta ON t.track_id = ta.track_id
        JOIN Artists a ON ta.artist_id = a.artist_id
        WHERE t.title LIKE %s
    """

    params = [f"%{track_keyword}%"]

    if artist_keyword:
        base_query += " AND a.name LIKE %s"
        params.append(f"%{artist_keyword}%")

    base_query += "ORDER BY t.popularity LIMIT 10"

    cursor.execute(base_query, tuple(params))
    result = cursor.fetchall()
    cursor.close()

    # convert ms to secs for readability in frontend
    for r in result:
        r["duration"] = r.pop("duration_ms") // 1000

    return result

def search_artists(keyword: str):
    '''
    Searches for artists with `keyword` in their name. Sorts by popularity,
    
    :param keyword: the artist name to search for
    :type keyword: str

    :returns result: List[dict[artist_id: int, name: str, popularity: int]]
    '''

    cursor = current_app.db.cursor(dictionary=True)
    query = """
        SELECT 
            artist_id,
            name,
            popularity
        FROM Artists
        WHERE name LIKE %s
        ORDER BY popularity DESC;
    """

    like_pattern = f"%{keyword}%"
    cursor.execute(query, (like_pattern,))

    result = cursor.fetchall()
    cursor.close()

    return result

def artist_page_data(artist_id: int):
    '''
    Returns all the data needed to construct an artist page in the frontend.
    Only returns the 100 most popular songs of the artist.
    
    :param artist_id: the id of the artist for whom to make a page
    :type artist_id: int

    :returns data: dict[name: str, tracks: List[dict[track_id, title, duration (secs), explicit]], \
        popularity: int]
    '''

    cursor = current_app.db.cursor(dictionary=True)

    artist_query = """
        SELECT name, popularity
        FROM Artists
        WHERE artist_id = %s;
    """
    cursor.execute(artist_query, (artist_id,))
    artist = cursor.fetchone()

    if not artist:
        cursor.close()
        return None

    # Get tracks by this artist
    tracks_query = """
        SELECT 
            t.track_id,
            t.title,
            t.duration_ms,
            t.explicit
        FROM Tracks t
        JOIN TrackArtists ta ON t.track_id = ta.track_id
        WHERE ta.artist_id = %s
        ORDER BY t.popularity DESC
        LIMIT 100;
    """

    cursor.execute(tracks_query, (artist_id,))
    tracks = cursor.fetchall()

    for track in tracks:
        track["duration"] = track.pop("duration_ms") // 1000

    cursor.close()

    return {
        "artist_info": artist,
        "tracks": tracks
    }

def user_page_data(user_id: int):
    '''
    Returns all data needed to contrsuct a user's page (a general user not the current user).
    
    :param user_id: the id of the user for whom to make a page
    :type user_id: int

    :returns data: dict[username: str, pfp_color: str, liked_tracks: List[dict[track_id, title, duration (secs), \
        artists: List[name: str]]], friends: List[dict[friend_id, friend_name]]]
    '''

    cursor = current_app.db.cursor(dictionary=True)

    # base user info
    user_query = """
        SELECT username, pfp_color
        FROM Users
        WHERE user_id = %s;
    """
    cursor.execute(user_query, (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.close()
        return None


    # get liked tracks
    liked_tracks_query = """
        SELECT
            t.track_id,
            t.title,
            t.duration_ms
        FROM TrackLikes tl
        JOIN Tracks t ON tl.track_id = t.track_id
        WHERE tl.user_id = %s;
    """

    cursor.execute(liked_tracks_query, (user_id,))
    liked_tracks = cursor.fetchall()

    # for each liked track, get all of its artists
    for track in liked_tracks:
        artist_query = """
            SELECT a.name
            FROM Artists a
            JOIN TrackArtists ta ON a.artist_id = ta.artist_id
            WHERE ta.track_id = %s;
        """
        cursor.execute(artist_query, (track["track_id"],))
        artists = cursor.fetchall()

        track["artists"] = [artist["name"] for artist in artists]

        track["duration"] = track.pop("duration_ms") // 1000

    friends_query = """
        SELECT 
            u.user_id AS friend_id,
            u.username AS friend_name
        FROM Friendships f
        JOIN Users u ON f.friend_id = u.user_id
        WHERE f.user_id = %s;
    """
    cursor.execute(friends_query, (user_id,))
    friends = cursor.fetchall()

    cursor.close()

    return {
        "user_info": user,
        "liked_tracks": liked_tracks,
        "friends": friends
    }

def track_page_data(track_id: int):
    '''
    Returns all data needed to construct a track page (just comments and general track info really).
    
    :param track_id: the id of the track for which to make a page
    :type track_id: int

    :returns data: dict[track_info: dict[title, release_date, duration (secs), explicit, key_signature, popularity, \
        liked], comments: List[dict[username, content, created_at]]]
    '''

    cursor = current_app.db.cursor(dictionary=True)

    # Get base track info
    track_query = """
        SELECT
            t.title,
            t.release_date,
            t.duration_ms,
            t.explicit,
            t.key_signature,
            t.popularity,
            EXISTS (
                SELECT 1
                FROM TrackLikes tl
                WHERE tl.track_id = t.track_id
                AND tl.user_id = %s
            ) AS liked
        FROM Tracks t
        WHERE t.track_id = %s;
    """
    cursor.execute(track_query, (track_id,))
    track = cursor.fetchone()

    if not track:
        cursor.close()
        return None

    track["duration"] = track.pop("duration_ms") // 1000


    # Get comments
    comments_query = """
        SELECT
            u.username,
            c.content,
            c.created_at
        FROM Comments c
        JOIN Users u ON c.user_id = u.user_id
        WHERE c.track_id = %s
        ORDER BY c.created_at DESC;
    """

    cursor.execute(comments_query, (track_id,))
    comments = cursor.fetchall()

    cursor.close()

    return {
        "track_info": track,
        "comments": comments
    }

def top_3_artists():
    '''
    Extracts the three artists the user has liked the most.

    :returns results: [
        {
            artist_id: int,
            name: str,
            like_count: int
        }
    ] \
    or List[dict[artist_id: int, name: str, like_count: int]]

    '''

    user_id = session['user_id']
    cursor = current_app.db.cursor(dictionary=True)

    query = """
        SELECT 
            a.artist_id,
            a.name,
            COUNT(tl.track_id) AS like_count
        FROM TrackLikes tl
        JOIN TrackArtists ta ON tl.track_id = ta.track_id
        JOIN Artists a ON ta.artist_id = a.artist_id
        WHERE tl.user_id = %s
        GROUP BY a.artist_id, a.name
        ORDER BY like_count DESC
        LIMIT 3;
    """

    cursor.execute(query, (user_id,))
    results = cursor.fetchall()

    return results

def top_3_genres():
    '''
    Finds the top 3 most liked genres of the user.

    :returns results: List[dict[genre_name: str, liked_count: int]] or \
    [
        {
            genre_name: str,
            liked_count: int
        }
    ]
    '''

    user_id = session["user_id"]
    cursor = current_app.db.cursor(dictionary=True)

    query = """
    SELECT 
        g.genre_name,
        COUNT(tl.track_id) AS liked_count
    FROM TrackLikes tl
    JOIN Tracks t ON tl.track_id = t.track_id
    JOIN ArtistGenres ag ON ag.artist_id = (
        SELECT ta.artist_id
        FROM TrackArtists ta
        WHERE ta.track_id = t.track_id
        LIMIT 1
    )
    JOIN Genres g ON ag.genre_id = g.genre_id
    WHERE tl.user_id = %s
    GROUP BY g.genre_id, g.genre_name
    ORDER BY liked_count DESC
    LIMIT 3;
    """

    cursor.execute(query, (user_id,))
    return cursor.fetchall()

def calculate_obscurity():
    '''
    Calculates the obscurity of a user's liked tracks. Finds the average popularity of liked tracks, \
        then subtracts that from 100. round(100 - avg(popularity), 2).
    
    :returns result: Float from 0 to 100. A return value of `x` is represented as `x%` obscure.
    '''

    user_id = session["user_id"]
    cursor = current_app.db.cursor(dictionary=True)

    query = """
        SELECT AVG(t.popularity) AS avg_popularity
        FROM TrackLikes tl
        JOIN Tracks t ON tl.track_id = t.track_id
        WHERE tl.user_id = %s;
    """

    cursor.execute(query, (user_id,))
    row = cursor.fetchone()

    if not row or row["avg_popularity"] is None:
        return 0.0  # no liked tracks

    obscurity = round(100 - float(row["avg_popularity"]), 2)
    return obscurity

def calculate_music_age():
    '''
    Calculates the average age of the user's liked songs.

    :returns result: integer value that is the users music age in years.
    '''

    user_id = session["user_id"]
    cursor = current_app.db.cursor(dictionary=True)

    query = """
        SELECT AVG(YEAR(CURDATE()) - YEAR(t.release_date)) AS avg_age
        FROM TrackLikes tl
        JOIN Tracks t ON tl.track_id = t.track_id
        WHERE tl.user_id = 1
        AND t.release_date IS NOT NULL;
    """

    cursor.execute(query, (user_id,))
    row = cursor.fetchone()

    if not row or row["avg_age"] is None:
        return 0  # no liked songs

    return int(round(row["avg_age"]))

FEATURE_RANGES = {
    "mode": (0,1),
    "danceability": (0, 1),
    "energy": (0, 1),
    "loudness": (-60, 5.4),
    "speechiness": (0, 1),
    "acousticness": (0, 1),
    "instrumentalness": (0, 1),
    "liveness": (0, 1),
    "valence": (0, 1),
    "tempo": (0, 246)
}

def normalize_feature(value, min_val, max_val):
    '''Required for features not on 0-1 scale for comparability.'''
    return (value - min_val) / (max_val - min_val)

FEATURE_COLUMNS = [
    "mode",
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "instrumentalness",
    "liveness",
    "speechiness",
    "loudness"
]

def get_taste_profile(user_id: int) -> np.array:
    '''
    Returns the user's "taste profile", computed as the average of the following
    attributes over all tracks they have liked:
    [mode, danceability, energy, loudness, speechiness, acousticness,
     instrumentalness, liveness, valence, tempo]

    :returns: a vector of the average value of characteristic track attributes.
    :rtype: np.array
    '''

    cursor = current_app.db.cursor(dictionary=True)

    query = """
        SELECT
            AVG(t.mode)                AS mode,
            AVG(t.danceability)        AS danceability,
            AVG(t.energy)              AS energy,
            AVG(t.loudness)            AS loudness,
            AVG(t.speechiness)         AS speechiness,
            AVG(t.acousticness)        AS acousticness,
            AVG(t.instrumentalness)    AS instrumentalness,
            AVG(t.liveness)            AS liveness,
            AVG(t.valence)             AS valence,
            AVG(t.tempo)               AS tempo,
        FROM TrackLikes tl
        JOIN Tracks t ON tl.track_id = t.track_id
        WHERE tl.user_id = %s;
    """

    cursor.execute(query, (user_id,))
    row = cursor.fetchone()
    cursor.close()

    if not row or all(v is None for v in row.values()):
        # no liked tracks
        return np.zeros(11)

    # final vector
    taste_vector = np.array([
        row["mode"],
        row["danceability"],
        row["energy"],
        row["loudness"],
        row["speechiness"],
        row["acousticness"],
        row["instrumentalness"],
        row["liveness"],
        row["valence"],
        row["tempo"]
    ], dtype=float)

    normalized = []
    # normalize features for comparability
    for feature, value in zip(FEATURE_COLUMNS, taste_vector):
        min_v, max_v = FEATURE_RANGES[feature]
        normalized.append(normalize_feature(value, min_v, max_v))

    return normalized

def cos_sim(x1: np.array, x2: np.array) -> float:
    '''
    Computes the cosine similarity of x1 and x2. 0 = no similarity, 1 = same norm. 
    It will always fall between 0 and 1 here because the features in Tracks are all non-negative.
    '''
    denom = norm(x1) * norm(x2)
    if denom == 0:  # check for div by zero errors
        return 0
    
    return np.dot(x1, x2) / denom

def get_compatibility(friend_id: int) -> float:
    '''
    Docstring for get_compatibility
    
    :param friend_id: The id of the friend with whom to test your compatibility
    :type friend_id: int
    :return: the "percent" compatibile. .45 corresponds to 45% compatible.
    :rtype: float
    '''
    user_id = session["user_id"]
    user_profile = get_taste_profile(user_id)
    friend_profile = get_taste_profile(friend_id)
    sim = cos_sim(user_profile, friend_profile)

    return sim

def find_soulmate():
    '''
    Computes compatibility with all friends and just returns the friend with the highest.

    :returns results: dict[friend_id: int, username: str]
    '''
    
    user_id = session["user_id"]
    cursor = current_app.db.cursor(dictionary=True)

    # get all friends
    query = """
        SELECT 
            u.user_id AS friend_id,
            u.username
        FROM Friendships f
        JOIN Users u ON (
            (f.user_id_1 = %s AND f.user_id_2 = u.user_id)
            OR
            (f.user_id_2 = %s AND f.user_id_1 = u.user_id)
        )
    """
    cursor.execute(query, (user_id, user_id))
    friends = cursor.fetchall()

    if not friends:
        return {}  # has no friends

    # find most compatible friend
    best_friend = None
    best_score = -1

    for friend in friends:
        friend_id = friend["friend_id"]
        score = get_compatibility(friend_id)

        if score > best_score:
            best_score = score
            best_friend = friend

    return best_friend if best_friend else {}

def recommend_friend():
    '''
    Recommend a friend of a friend that the user is not currently friends with. Looks through every friend of every \
    friend the user currently has (and goes no deeper. Walk = length 2), and finds the user with the highest \
    compatibility to the user. This is deterministic. The answer won't change unless the user befriends the first \
    result and asks for another recommendation.

    :returns result: {friend_id: int, username: str}
    '''

    cursor = current_app.db.cursor(dictionary=True)
    user_id = session["user_id"]
    
    # current friends
    cursor.execute("""
        SELECT 
            CASE 
                WHEN user_id = %s THEN friend_id
                ELSE user_id
            END AS friend_id
        FROM Friendships
        WHERE user_id = %s OR friend_id = %s
    """, (user_id, user_id, user_id))

    direct_friends = {row["friend_id"] for row in cursor.fetchall()}

    if not direct_friends:
        return None  # no friends so not recommendations

    direct_friends.add(user_id)  # prevent self-recommendation

    # find friends of friends
    placeholder = ",".join(["%s"] * len(direct_friends))

    query = f"""
        SELECT DISTINCT
            CASE
                WHEN user_id IN ({placeholder}) THEN friend_id
                ELSE user_id
            END AS foaf_id
        FROM Friendships
        WHERE user_id IN ({placeholder}) OR friend_id IN ({placeholder})
    """

    cursor.execute(query, tuple(direct_friends) * 3)
    candidates = {row["foaf_id"] for row in cursor.fetchall()}

    # remove direct friends + self
    candidates = candidates - direct_friends

    if not candidates:
        return None

    best_id = None
    best_score = -1

    for candidate_id in candidates:
        score = get_compatibility(candidate_id)
        if score > best_score:
            best_score = score
            best_id = candidate_id

    if best_id is None:
        return None

    cursor.execute("""
        SELECT user_id AS friend_id, username
        FROM Users
        WHERE user_id = %s
    """, (best_id,))

    return cursor.fetchone()

def get_track_vector(cursor, track_id):
    cols = ", ".join(FEATURE_COLUMNS)
    cursor.execute(f"""
        SELECT {cols}
        FROM Tracks
        WHERE track_id = %s
    """, (track_id,))

    row = cursor.fetchone()

    if row:
        normalized = []
        # normalize features for comparability
        for feature, value in zip(FEATURE_COLUMNS, row):
            min_v, max_v = FEATURE_RANGES[feature]
            normalized.append(normalize_feature(value, min_v, max_v))
    else:
        return None

    return normalized


def get_random_sample(cursor, sample_size):
    cols = ", ".join(["track_id", "title"] + FEATURE_COLUMNS)

    cursor.execute(f"""
        SELECT {cols}
        FROM Tracks
        ORDER BY RAND()
        LIMIT %s
    """, (sample_size,))

    return cursor.fetchall()


def get_similar_tracks(track_id, sample_size=2000, top_k=50, return_n=10):
    '''
    Non-deterministically finds `return_n` (Default 10) songs that are similar to `track_id` using cosine similarity \
    between vectors of the musical features of tracks. Samples 2000 songs, finds the top `top_k` that this track is \
    similar to, then returns a random 10 songs from these 50 (default for `top_k`).
    
    :param track_id: the id of the track for which to find similar songs
    :param sample_size: the size of the random sample from our database to test similarity against
    :param top_k: the size of the sample of songs that are similar to track_id from which to sample the final 10
    :param return_n: the final amount of similar songs to return

    :returns results: the top `return_n` similar songs to this track. List[dict[track_id: int, title: str]]
    '''

    cursor = current_app.db.cursor(dictionary=True)

    target_vector = get_track_vector(cursor, track_id)

    if not target_vector:
        cursor.close()
        raise ValueError(f"Track {track_id} not found.")

    # random sample of tracks to compare against
    sample = get_random_sample(cursor, sample_size)

    similarities = []

    for row in sample:
        sid = row['track_id']
        stitle = row['title']

        # skip self
        if sid == track_id:
            continue

        vector = row[2:]

        normalized = []
        # normalize features for comparability
        for feature, value in zip(FEATURE_COLUMNS, row):
            min_v, max_v = FEATURE_RANGES[feature]
            normalized.append(normalize_feature(value, min_v, max_v))

        sim = cos_sim(target_vector, normalized)
        similarities.append((sid, stitle, sim))

    # sort by similarity and get the top_k songs then randomly draw return_n
    similarities.sort(key=lambda x: x[2], reverse=True)
    top_candidates = similarities[:top_k]
    final_selection = random.sample(top_candidates, min(return_n, len(top_candidates)))

    cursor.close()

    return [{"track_id": track_id, "title": title} for track_id, title, _ in final_selection]

def create_discovery_playlist():
    '''
    Creates a collection of 20 songs that are from genres that the user has not liked before.
    Non-deterministic: randomizes order of the dataset, the first 20 songs with artists whose genres are not \
    among the user's liked genres are returned. The artists of each track are returned as a string. No metadata is provided.

    :returns results: List[dict[track_id: int, title: str, artists: str]]
    AKA [
        {
            track_id: int,
            title: str,
            artists: str
        }
    ]
    '''

    user_id = session["user_id"]
    cursor = current_app.db.cursor(dictionary=True)

    # genres the user has liked
    cursor.execute(
        '''
        SELECT DISTINCT ag.genre_id
        FROM TrackLikes tl
        JOIN TrackArtists ta ON tl.track_id = ta.track_id
        JOIN ArtistGenres ag ON ta.artist_id = ag.artist_id
        WHERE tl.user_id = %s
        ''',
        (user_id,)
    )

    excluded_genres = [row["genre_id"] for row in cursor.fetchall()]

    # if user hasn't liked anything
    if not excluded_genres:
        genre_filter = ""
        params = []
    else:
        placeholders = ", ".join(["%s"] * len(excluded_genres))
        genre_filter = f"WHERE ag.genre_id NOT IN ({placeholders})"
        params = excluded_genres

    # look for 20 songs with optimized randomization
    query = f'''
        SELECT
            t.track_id,
            t.title,
            GROUP_CONCAT(DISTINCT a.name SEPARATOR ', ') AS artists
        FROM Tracks t
        JOIN TrackArtists ta ON t.track_id = ta.track_id
        JOIN Artists a ON ta.artist_id = a.artist_id
        JOIN ArtistGenres ag ON a.artist_id = ag.artist_id
        {genre_filter}
          AND t.track_id >= (
            SELECT FLOOR(
                (SELECT MIN(track_id) FROM Tracks) +
                RAND() * (
                    (SELECT MAX(track_id) FROM Tracks) -
                    (SELECT MIN(track_id) FROM Tracks)
                )
            )
        )
        GROUP BY t.track_id
        LIMIT 20;
    '''

    cursor.execute(query, params)
    results = cursor.fetchall()

    return results

def create_dashboard():
    '''
    Generates a radar/web plot of the musical attributes the user most listens to.
    This web plot has 8 variables which are the features in the FEATURE_COLUMNS variable. (i.e. danceability, valence)
    If the user's theme in the Preferences table is 'light', axes are black and bg is white. If 'dark', \
        use a black bg and white axes. The color of the web itself is #1DB954.

    Stores the figure as a png with dpi 200 in the static/ folder.
    Returns name of the file in the static folder.
    '''

    user_id = session["user_id"]
    cursor = current_app.db.cursor(dictionary=True)

    pass
