from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash

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
            query = "INSERT INTO Users (username, email, password_hash) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, email, hashed_pw))
            current_app.db.commit()
            
            # preferences insertion
            user_id = cursor.lastrowid
            query_pref = "INSERT INTO Preferences (user_id) VALUES (%s, %s, %s)"
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
            - discovery: generate a discovery playlist for the user
            - recommend_friend: recommend a friend of a friend based on similarity
                - Requires `friend_id` attr. The friend of whom to find a friend
    '''
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    user_id = session['user_id']
    liked_songs = []
    friends = []
    
    # find liked songs
    query = "SELECT t.* FROM Tracks t JOIN TrackLikes tl ON t.track_id = tl.track_id WHERE tl.user_id = %s"
    cursor = current_app.db.cursor(dictionary=True)
    cursor.execute(query, (user_id))
    liked_songs = cursor.fetchall()
    # find friends
    query = "SELECT u.* FROM Users u " \
            "JOIN Friendships f ON" \
            "(u.user_id = f.user_id1 AND f.user_id2 = %s) OR (u.user_id = f.user_id2 AND f.user_id1 = %s)"
    cursor.execute(query, (user_id))
    friends = cursor.fetchall()
    cursor.close()

    # TODO: implement queries like friend compatibility or discovery playlist or insights dashboard

    dashboard_data = {
        'liked_songs': [], 
        'top_genres': [],
        'friend_recommendations': []
    }

    return render_template('home.html',
                           liked_songs=liked_songs,
                           friends=friends)


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
        - liked (bool): if a user liked the track. False if this POST is about a comment.
    
    Information sent to frontend:

        track = {
            title: str,
            release_date: str,
            duration: int (secs),
            explicit: boolean,
            key_signature: int,
            popularity: int
        }
        
        comments = [
            {
                username: str,
                content: str,
                created_at: str
            }
        ]
    '''
    if request.method == 'POST':
        # TODO: Add comment or like
        pass

    # TODO: implement function to fetch track info and comments
    page_data = track_page_data(track_id)

    return render_template('track.html',
                           track=page_data["track_info"],
                           comments=page_data["comments"])

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
        ORDER BY t.popularity DESC;
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

    :returns data: dict[title, release_date, duration (secs), explicit, key_signature, popularity, \
        comments: List[dict[username, content, created_at]]]
    '''

    cursor = current_app.db.cursor(dictionary=True)

    # Get base track info
    track_query = """
        SELECT
            title,
            release_date,
            duration_ms,
            explicit,
            key_signature,
            popularity
        FROM Tracks
        WHERE track_id = %s;
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
