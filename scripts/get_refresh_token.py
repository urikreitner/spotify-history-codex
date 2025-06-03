#!/usr/bin/env python3
"""Utility to generate a Spotify refresh token."""
import os
import spotipy.util as util

TOKEN = util.prompt_for_user_token(
    username=os.getenv("SPOTIFY_USER"),
    scope="user-read-recently-played",
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="http://localhost:8888/callback",
)
print(TOKEN)
