# logger_recent.py — store recent plays + metadata in SQLite (with diagnostics + heartbeat)
import os, sqlite3, time, json
from pathlib import Path
from datetime import datetime, timezone
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ---------- ABSOLUTE DB PATH (critical) ----------
DB = Path(__file__).with_name("data.db").resolve()
env_path = Path(__file__).with_name(".env")
load_dotenv(env_path)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=os.getenv("SPOTIPY_SCOPE", "user-read-recently-played user-library-read user-top-read"),
    open_browser=True,
    cache_path=str(Path(__file__).with_name(".spotipy-cache")),
    show_dialog=False,
    requests_timeout=30,
))

def db_init(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS plays(
        played_at TEXT PRIMARY KEY,   -- ISO8601 UTC
        track_id  TEXT NOT NULL,
        context   TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS tracks(
        id TEXT PRIMARY KEY,
        name TEXT,
        duration_ms INTEGER,
        popularity INTEGER,
        album_id TEXT,
        is_saved INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS albums(
        id TEXT PRIMARY KEY,
        name TEXT,
        release_date TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS artists(
        id TEXT PRIMARY KEY,
        name TEXT,
        popularity INTEGER,
        followers INTEGER,
        genres TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS track_artists(
        track_id TEXT,
        artist_id TEXT,
        PRIMARY KEY(track_id, artist_id)
    )""")
    # for diagnostic heartbeats
    cur.execute("""CREATE TABLE IF NOT EXISTS runs(
        ran_at TEXT PRIMARY KEY,   -- ISO8601 UTC
        note   TEXT
    )""")
    conn.commit()

def upsert_track(conn, t):
    cur = conn.cursor()
    cur.execute("""INSERT INTO tracks(id,name,duration_ms,popularity,album_id)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     name=excluded.name,
                     duration_ms=excluded.duration_ms,
                     popularity=excluded.popularity,
                     album_id=excluded.album_id
                """, (t["id"], t["name"], t.get("duration_ms") or 0, t.get("popularity") or 0, t["album"]["id"]))
    conn.commit()

def upsert_album(conn, a):
    cur = conn.cursor()
    cur.execute("""INSERT INTO albums(id,name,release_date)
                   VALUES(?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     name=excluded.name,
                     release_date=excluded.release_date
                """, (a["id"], a["name"], a.get("release_date") or None))
    conn.commit()

def upsert_artist(conn, a):
    cur = conn.cursor()
    cur.execute("""INSERT INTO artists(id,name,popularity,followers,genres)
                   VALUES(?,?,?,?,?)
                   ON CONFLICT(id) DO UPDATE SET
                     name=excluded.name,
                     popularity=excluded.popularity,
                     followers=excluded.followers,
                     genres=excluded.genres
                """, (a["id"], a["name"], a.get("popularity") or 0,
                      (a.get("followers") or {}).get("total") or 0,
                      json.dumps(a.get("genres") or [])))
    conn.commit()

def upsert_track_artists(conn, track_id, artist_ids):
    cur = conn.cursor()
    for aid in artist_ids:
        cur.execute("""INSERT OR IGNORE INTO track_artists(track_id, artist_id)
                       VALUES(?,?)""", (track_id, aid))
    conn.commit()

def mark_saved_flags(conn, track_ids):
    if not track_ids: return
    # Spotify allows up to 50 at a time
    for i in range(0, len(track_ids), 50):
        batch = track_ids[i:i+50]
        flags = sp.current_user_saved_tracks_contains(batch)
        cur = conn.cursor()
        for tid, flag in zip(batch, flags):
            cur.execute("UPDATE tracks SET is_saved=? WHERE id=?", (1 if flag else 0, tid))
        conn.commit()

def log_recently_played(conn):
    resp = sp.current_user_recently_played(limit=50)
    items = resp.get("items", []) or []
    print(f"Fetched {len(items)} recent plays")

    new_track_ids = set()
    inserted_plays = 0

    for it in items:
        played_at = it["played_at"]   # ISO8601
        # normalize to UTC ISO w/ Z suffix
        dt = datetime.fromisoformat(played_at.replace("Z","+00:00")).astimezone(timezone.utc)
        played_iso = dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00","Z")

        t = it.get("track") or {}
        if not t or not t.get("id"):
            continue

        # upsert track/album/artists
        upsert_track(conn, t)
        upsert_album(conn, t["album"])

        artist_ids = [a["id"] for a in t.get("artists", []) if a.get("id")]
        if artist_ids:
            arts = sp.artists(artist_ids)["artists"]
            for a in arts:
                upsert_artist(conn, a)
            upsert_track_artists(conn, t["id"], artist_ids)

        # insert play row if new
        ctx = (it.get("context") or {}).get("type")
        try:
            conn.execute("INSERT INTO plays(played_at, track_id, context) VALUES(?,?,?)",
                         (played_iso, t["id"], ctx))
            inserted_plays += 1
        except sqlite3.IntegrityError:
            pass  # already logged

        new_track_ids.add(t["id"])

    # mark saved flags for all recent tracks
    mark_saved_flags(conn, list(new_track_ids))
    conn.commit()
    print(f"Inserted plays this run: {inserted_plays}")
    print("Done.")

# --------- small helpers for diagnostics ----------
def count_rows(conn, table):
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:
        return 0

def latest_play_ts(conn):
    row = conn.execute("SELECT MAX(played_at) FROM plays").fetchone()
    return row[0] if row and row[0] else None

# ---------------- RUN / DIAGNOSTICS ----------------
if __name__ == "__main__":
    print(f"USING_DB: {DB}")  # This absolute path must match your API's DB path.

    before_mtime = DB.stat().st_mtime if DB.exists() else None
    before_mtime_iso = (
        datetime.fromtimestamp(before_mtime, tz=timezone.utc).isoformat() if before_mtime else None
    )

    with sqlite3.connect(DB) as conn:
        db_init(conn)

        # before counts
        b_plays   = count_rows(conn, "plays")
        b_tracks  = count_rows(conn, "tracks")
        b_artists = count_rows(conn, "artists")
        b_albums  = count_rows(conn, "albums")
        b_map     = count_rows(conn, "track_artists")
        prev_latest = latest_play_ts(conn)

        # ingest
        log_recently_played(conn)

        # after counts
        a_plays   = count_rows(conn, "plays")
        a_tracks  = count_rows(conn, "tracks")
        a_artists = count_rows(conn, "artists")
        a_albums  = count_rows(conn, "albums")
        a_map     = count_rows(conn, "track_artists")
        new_latest = latest_play_ts(conn)

        # heartbeat to guarantee mtime bump even if no new plays
        heartbeat = datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        conn.execute("INSERT OR REPLACE INTO runs(ran_at, note) VALUES(?, ?)",
                     (heartbeat, "logger_recent heartbeat"))
        conn.commit()

    after_mtime = DB.stat().st_mtime
    after_mtime_iso = datetime.fromtimestamp(after_mtime, tz=timezone.utc).isoformat()

    print("=== DIAGNOSTIC ===")
    print(f"DB path        : {DB}")
    print(f"mtime before   : {before_mtime_iso}")
    print(f"mtime after    : {after_mtime_iso}")
    print(f"plays          : {b_plays} -> {a_plays} (Δ {a_plays - b_plays})")
    print(f"tracks         : {b_tracks} -> {a_tracks} (Δ {a_tracks - b_tracks})")
    print(f"artists        : {b_artists} -> {a_artists} (Δ {a_artists - b_artists})")
    print(f"albums         : {b_albums} -> {a_albums} (Δ {a_albums - b_albums})")
    print(f"track_artists  : {b_map} -> {a_map} (Δ {a_map - b_map})")
    print(f"latest played@ : {prev_latest} -> {new_latest}")
    print("==================")
