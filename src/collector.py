#!/usr/bin/env python3
import os
import sqlite3
import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# determine monthly DB path
now = datetime.datetime.utcnow()
db_name = f"history_{now.strftime('%Y%m')}.db"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", db_name)

conn = sqlite3.connect(DB_PATH)
conn.execute("""CREATE TABLE IF NOT EXISTS plays (
    played_at TEXT PRIMARY KEY,
    track_id  TEXT,
    track     TEXT,
    artist    TEXT,
    ms_played INTEGER
)""")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://localhost:8888/callback",
    scope="user-read-recently-played",
    cache_path="/tmp/.spotify-cache"
))

for item in sp.current_user_recently_played(limit=50)["items"]:
    row = (
        item["played_at"],
        item["track"]["id"],
        item["track"]["name"],
        ", ".join(a["name"] for a in item["track"]["artists"]),
        item["ms_played"]
    )
    conn.execute("INSERT OR IGNORE INTO plays VALUES (?,?,?,?,?)", row)

conn.commit()
