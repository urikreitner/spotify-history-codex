#!/usr/bin/env python3
import argparse
import datetime
import glob
import json
import os
import sqlite3
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)

SCHEMA = """CREATE TABLE IF NOT EXISTS plays (
    played_at TEXT PRIMARY KEY,
    track_id  TEXT,
    track     TEXT,
    artist    TEXT,
    ms_played INTEGER,
    genre     TEXT
)"""


def get_conn(dt: datetime.datetime, conns: Dict[str, sqlite3.Connection]) -> sqlite3.Connection:
    month = dt.strftime("%Y%m")
    if month not in conns:
        path = os.path.join(DATA_DIR, f"history_{month}.db")
        conn = sqlite3.connect(path)
        conn.execute(SCHEMA)
        # add genre column if missing in legacy DB
        cols = [c[1] for c in conn.execute("PRAGMA table_info(plays)").fetchall()]
        if "genre" not in cols:
            conn.execute("ALTER TABLE plays ADD COLUMN genre TEXT")
        conns[month] = conn
        logger.info("Opened %s", path)
    return conns[month]


def process_file(fname: str, conns: Dict[str, sqlite3.Connection]) -> int:
    with open(fname, "r", encoding="utf-8") as f:
        items = json.load(f)
    logger.info("Loaded %s (%d items)", fname, len(items))
    inserted = 0
    for entry in items:
        # parse endTime as UTC
        dt = datetime.datetime.strptime(entry["endTime"], "%Y-%m-%d %H:%M")
        dt = dt.replace(tzinfo=datetime.timezone.utc)
        played_at = dt.isoformat()

        track_id = entry.get("spotifyTrackUri") or entry.get("spotifyEpisodeUri")
        if track_id and ":" in track_id:
            track_id = track_id.rsplit(":", 1)[-1]
        track = entry.get("trackName") or entry.get("episodeName")
        artist = entry.get("artistName") or entry.get("episodeShowName")
        ms_played = entry.get("msPlayed") or entry.get("ms_played")

        genre = ""
        row = (played_at, track_id, track, artist, ms_played, genre)

        conn = get_conn(dt, conns)
        cur = conn.execute(
            "INSERT OR IGNORE INTO plays VALUES (?,?,?,?,?,?)",
            row,
        )
        inserted += cur.rowcount
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Back-fill DB from Streaming History JSON")
    parser.add_argument("glob", help="Glob path to Streaming_History JSON files")
    args = parser.parse_args()

    files = sorted(glob.glob(args.glob))
    if not files:
        parser.error("No files matched")

    conns: Dict[str, sqlite3.Connection] = {}
    total_inserted = 0
    for fname in files:
        total_inserted += process_file(fname, conns)

    for conn in conns.values():
        conn.commit()
        conn.close()
    logger.info("Inserted %d new plays", total_inserted)


if __name__ == "__main__":
    main()
