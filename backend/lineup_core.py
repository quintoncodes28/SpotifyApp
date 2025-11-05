import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import json
import numpy as np
import pandas as pd
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import re  # <-- you had this

# ---------- Setup ----------
BASE_DIR = Path(__file__).resolve().parent
DB = BASE_DIR / "data.db"
HISTORY_JSON = BASE_DIR / "history.json"
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope=os.getenv("SPOTIPY_SCOPE", "user-top-read"),
    open_browser=True,
    cache_path=str(BASE_DIR / ".spotipy-cache"),
    show_dialog=False,
    requests_timeout=30,
))

# ---------- Helpers ----------
def z(s: pd.Series) -> pd.Series:
    s = s.astype(float)
    mu, sd = s.mean(), s.std()
    if sd == 0 or np.isnan(sd):
        sd = 1.0
    return (s - mu) / sd

def _team_label_from_stats(avg_pop: float | None, avg_followers: float | None) -> str:
    """
    Map lineup 'fame' to a 5-tier label using avg artist popularity (0-100)
    and avg followers (log-scaled). Followers are log10-scaled and converted
    to a 0-100 band where ~10M followers ≈ 100.
    """
    ap = float(avg_pop or 0.0)
    af = float(avg_followers or 0.0)

    # followers score: log10 scaled into ~0..100 (10^7 -> 100)
    import math
    followers_score = 0.0
    if af > 0:
        followers_score = min(100.0, (math.log10(af) / 7.0) * 100.0)

    # combine: popularity weighted a bit more than followers
    fame = 0.6 * ap + 0.4 * followers_score

    # 5-tier thresholds
    if fame >= 85:
        return "Super Nova"
    if fame >= 70:
        return "Star Studded"
    if fame >= 55:
        return "Established"
    if fame >= 40:
        return "Rising"
    return "Underground"


def extract_album_image(track: dict) -> str | None:
    """Safely extract the album image URL from a Spotify track object."""
    if not isinstance(track, dict):
        return None
    album = track.get("album")
    if not album:
        return None
    images = album.get("images", [])
    if isinstance(images, list) and len(images) > 0:
        return images[0].get("url")
    return None


# ---------- Album cover cache + Spotify fallback ----------
_cover_cache = {}

def get_album_cover_fallback(track_id: str) -> str | None:
    """Fetch album cover from Spotify if missing in local DB."""
    if not track_id:
        return None
    if track_id in _cover_cache:
        return _cover_cache[track_id]
    try:
        track = sp.track(track_id)
        images = track.get("album", {}).get("images", [])
        if images:
            url = images[0]["url"]
            _cover_cache[track_id] = url
            return url
    except Exception:
        return None
    return None


# ---------- Artist image cache (Spotify fallback) ----------
_artist_img_cache = {}

def get_artist_image(artist_id: str) -> str | None:
    """Fetch primary artist profile image URL from Spotify (cached)."""
    if not artist_id:
        return None
    if artist_id in _artist_img_cache:
        return _artist_img_cache[artist_id]
    try:
        a = sp.artist(artist_id)
        images = a.get("images", [])
        if images:
            url = images[0]["url"]
            _artist_img_cache[artist_id] = url
            return url
    except Exception:
        return None
    return None


# ---------- NEW: Refresh logger (recently played -> SQLite) ----------
def refresh_recent_plays(limit: int = 50) -> int:
    """
    Pull the last 'limit' recently-played tracks from Spotify and insert into local DB.
    Upserts by (played_at, track_id) so reruns are safe. Returns number of rows attempted.
    """
    # 1) Fetch from Spotify
    items = sp.current_user_recently_played(limit=limit).get("items", [])

    # 2) Ensure plays table exists with a uniqueness constraint
    with sqlite3.connect(DB) as conn:
        conn.execute("""
          CREATE TABLE IF NOT EXISTS plays (
            played_at TEXT NOT NULL,
            track_id  TEXT NOT NULL,
            context   TEXT,
            PRIMARY KEY (played_at, track_id)
          )
        """)
        rows = []
        for it in items:
            played_at = it.get("played_at")
            track = it.get("track", {}) or {}
            track_id = track.get("id")
            context = (it.get("context") or {}).get("type")
            if played_at and track_id:
                rows.append((played_at, track_id, context))

        if rows:
            conn.executemany(
                "INSERT OR IGNORE INTO plays (played_at, track_id, context) VALUES (?, ?, ?)",
                rows
            )
            conn.commit()

    return len(rows)


# ---------- ALL-TIME (Receiptify-style) ----------
def fetch_alltime_df() -> pd.DataFrame:
    items = sp.current_user_top_tracks(limit=50, time_range="long_term").get("items", [])
    if not items:
        return pd.DataFrame()

    rows = []
    for t in items:
        artists = ", ".join([a["name"] for a in t["artists"]])
        followers = np.mean([a.get("followers", {}).get("total", 0) for a in t["artists"]])
        pop = np.mean([a.get("popularity", 0) for a in t["artists"]])
        album_image_url = extract_album_image(t)

        # NEW: primary artist id + profile image
        primary_artist_id = t["artists"][0]["id"] if t.get("artists") else None
        artist_image_url = get_artist_image(primary_artist_id) if primary_artist_id else None

        rows.append({
            "track_id": t["id"],
            "track_name": t["name"],
            "popularity": t["popularity"],
            "artist_name": artists,
            "artist_pop": pop,
            "artist_followers": followers,
            "album_name": t["album"]["name"],
            "album_release_date": t["album"]["release_date"],
            "album_image_url": album_image_url,
            "artist_image_url": artist_image_url,  # <-- NEW
            "is_saved": 1.0,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["release_dt"] = pd.to_datetime(df["album_release_date"], errors="coerce", utc=True)
    now = pd.Timestamp.now(tz="UTC")
    df["days_since_release"] = (now - df["release_dt"]).dt.days
    dsr = df["days_since_release"].fillna(df["days_since_release"].median())
    df["z_recency"] = -(dsr - dsr.mean()) / (dsr.std() or 1.0)

    df["artist_followers_log"] = np.log1p(df["artist_followers"].fillna(0))
    df["z_popularity"] = z(df["popularity"].fillna(0))
    df["z_clout"] = 0.5 * z(df["artist_pop"].fillna(0)) + 0.5 * z(df["artist_followers_log"])
    df["z_affinity"] = z(df["is_saved"].fillna(0))

    w = {"z_popularity": 0.45, "z_clout": 0.25, "z_recency": 0.20, "z_affinity": 0.10}
    df["HIv2"] = sum(w[k] * df[k] for k in w)
    return df


# ---------- CURRENT (30-day, from logger DB) ----------
def fetch_current_df(days: int = 30) -> pd.DataFrame:
    if not DB.exists():
        return pd.DataFrame()

    with sqlite3.connect(DB) as conn:
        plays = pd.read_sql_query("SELECT played_at, track_id, context FROM plays", conn, parse_dates=["played_at"])
        tracks = pd.read_sql_query("SELECT * FROM tracks", conn)
        albums = pd.read_sql_query("SELECT * FROM albums", conn)
        tas = pd.read_sql_query("SELECT * FROM track_artists", conn)
        artists = pd.read_sql_query("SELECT * FROM artists", conn)

    if plays.empty:
        return pd.DataFrame()

    tracks.rename(columns={"id": "track_id"}, inplace=True)
    plays["played_at"] = pd.to_datetime(plays["played_at"], errors="coerce", utc=True)
    now = pd.Timestamp.utcnow()
    cutoff = now - pd.Timedelta(days=days)
    plays_window = plays.loc[plays["played_at"] >= cutoff].copy()
    if plays_window.empty:
        return pd.DataFrame()

    plays_window["date"] = plays_window["played_at"].dt.floor("D")
    plays_7d = plays_window[plays_window["played_at"] >= now - pd.Timedelta(days=7)].groupby("track_id").size().rename("plays_7d")
    plays_prev7d = plays_window[
        (plays_window["played_at"] < now - pd.Timedelta(days=7))
        & (plays_window["played_at"] >= now - pd.Timedelta(days=14))
    ].groupby("track_id").size().rename("plays_prev7d")
    plays_30d = plays_window.groupby("track_id").size().rename("plays_30d")
    days_played = plays_window.groupby("track_id")["date"].nunique().rename("distinct_days")
    diversity = plays_window.groupby("track_id")["context"].nunique().rename("contexts_n").fillna(0)

    df = tracks.merge(albums.rename(columns={"id": "album_id"}), on="album_id", how="left", suffixes=("_track", "_album"))
    df.rename(columns={"name_track": "track_name", "name_album": "album_name"}, inplace=True)

    if not artists.empty and not tas.empty:
        art = artists.rename(columns={"id": "artist_id"})
        ta = tas.merge(art, on="artist_id", how="left")
        # NEW: keep a primary artist id so we can fetch their profile image
        agg = ta.groupby("track_id").agg(
            artist_pop=("popularity", "mean"),
            artist_followers=("followers", "mean"),
            artist_name=("name", lambda x: ", ".join(x.unique())),
            primary_artist_id=("artist_id", "first"),  # <-- NEW
        ).reset_index()
        df = df.merge(agg, on="track_id", how="left")
    else:
        df["artist_pop"] = np.nan
        df["artist_followers"] = np.nan
        df["artist_name"] = "Unknown"
        df["primary_artist_id"] = None

    for s in [plays_7d, plays_prev7d, plays_30d, days_played, diversity]:
        df = df.merge(s, left_on="track_id", right_index=True, how="left")
    for c in ["plays_7d", "plays_prev7d", "plays_30d", "distinct_days", "contexts_n"]:
        df[c] = df[c].fillna(0)

    release_col = None
    for c in ["album_release_date", "release_date", "released_at"]:
        if c in df.columns:
            release_col = c
            break
    if release_col:
        df["release_dt"] = pd.to_datetime(df[release_col].astype(str), errors="coerce", utc=True)
    else:
        df["release_dt"] = pd.NaT

    # 🧩 Fetch album cover for each track
    df["album_image_url"] = df.apply(lambda r: get_album_cover_fallback(r.get("track_id")), axis=1)

    # 🧩 Fetch artist profile image for the primary artist
    df["artist_image_url"] = df["primary_artist_id"].apply(get_artist_image)

    df["artist_followers_log"] = np.log1p(df["artist_followers"].fillna(0))
    df["z_plays30"] = z(df["plays_30d"])
    df["z_momentum"] = z(df["plays_7d"] - df["plays_prev7d"])
    df["z_popularity"] = z(df["popularity"].fillna(0))
    df["z_clout"] = 0.5 * z(df["artist_pop"].fillna(0)) + 0.5 * z(df["artist_followers_log"])
    df["z_affinity"] = z(df["is_saved"].fillna(0))
    df["z_diversity"] = 0.5 * z(df["distinct_days"]) + 0.5 * z(df["contexts_n"])

    now_utc = pd.Timestamp.now(tz="UTC")
    df["days_since_release"] = (now_utc - df["release_dt"]).dt.days
    dsr = df["days_since_release"].fillna(df["days_since_release"].median())
    df["z_recency"] = -(dsr - dsr.mean()) / (dsr.std() or 1.0)

    w = {
        "z_plays30": 0.35,
        "z_momentum": 0.20,
        "z_popularity": 0.15,
        "z_clout": 0.10,
        "z_recency": 0.10,
        "z_affinity": 0.07,
        "z_diversity": 0.03,
    }
    df["HIv2"] = sum(w[k] * df[k] for k in w)
    return df


# ---------- Shared helpers ----------
POSITIONS = ["CF", "SS", "RF", "1B", "2B", "3B", "C", "LF", "P"]

# NEW: split regex + primary-artist normalizer
_SPLIT_RE = re.compile(r'\s*(?:,|&| and | x |×| feat\.?| featuring | ft\.?| with )\s*', re.IGNORECASE)

def primary_artist_name(name: str) -> str:
    """
    Normalize to a single primary artist key:
    - take the first artist before collab separators
    - collapse whitespace, casefold for case-insensitive match
    """
    if not isinstance(name, str) or not name.strip():
        return ""
    first = _SPLIT_RE.split(name)[0]
    key = re.sub(r"\s+", " ", first).strip().casefold()
    return key


def enforce_unique_artists_and_position(df: pd.DataFrame, top_n: int = 9) -> list[dict]:
    """Return list of dicts with unique *primary* artists and assigned positions."""
    if df is None or df.empty:
        return []

    work = df.copy()

    # Ensure columns exist
    if "artist_name" not in work.columns:
        work["artist_name"] = "Unknown"
    if "HIv2" not in work.columns:
        work["HIv2"] = 0.0

    # Build normalized primary-artist key
    work["primary_artist"] = work["artist_name"].map(primary_artist_name)

    # Rank by score, then drop duplicates by primary artist (keep the highest score)
    ranked = work.sort_values("HIv2", ascending=False, kind="stable").reset_index(drop=True)
    deduped = ranked.drop_duplicates(subset=["primary_artist"], keep="first").head(top_n)

    lineup = []
    for _, row in deduped.iterrows():
        pos = POSITIONS[len(lineup)] if len(lineup) < len(POSITIONS) else "-"
        cover = row.get("album_image_url") if isinstance(row.get("album_image_url"), str) else None
        artist_img = row.get("artist_image_url") if isinstance(row.get("artist_image_url"), str) else None

        lineup.append({
            "track": row.get("track_name") or "",
            "title": row.get("track_name") or "",
            "artist": row.get("artist_name") or "",
            "position": pos,
            "score": float(row.get("HIv2", 0.0)),
            "popularity": int(row.get("popularity", 0)) if not pd.isna(row.get("popularity", np.nan)) else 0,
            "track_id": row.get("track_id"),
            "album_cover": cover,
            "artist_image": artist_img,  # <-- NEW (used by frontend)
        })
        if len(lineup) >= top_n:
            break
    return lineup


def build_lineup(mode: str = "current") -> dict:
    if mode == "alltime":
        df = fetch_alltime_df()
        title = "ALL-TIME (Spotify Long-Term)"
    else:
        df = fetch_current_df(days=30)
        title = "CURRENT (30-Day Trend)"
    if df.empty:
        return {"mode": mode, "title": title, "lineup": [], "team_profile": None, "star_player": None, "saved": False}

    lineup = enforce_unique_artists_and_position(df, top_n=9)
    star = lineup[1] if len(lineup) > 1 else lineup[0] if lineup else None

    # --- NEW: compute 5-tier label from the selected 9
    team_profile = None
    try:
        ids = [it.get("track_id") for it in lineup if it.get("track_id")]
        if ids:
            sel = df[df["track_id"].isin(ids)]
            avg_pop = float(sel["artist_pop"].mean(skipna=True)) if "artist_pop" in sel.columns else 0.0
            avg_followers = float(sel["artist_followers"].mean(skipna=True)) if "artist_followers" in sel.columns else 0.0
            label = _team_label_from_stats(avg_pop, avg_followers)
            team_profile = {
                "label": label,
                "avg_artist_popularity": round(avg_pop, 1),
                "avg_artist_followers": int(avg_followers) if avg_followers == avg_followers else 0,
            }
    except Exception:
        team_profile = None
    # --- end NEW

    payload = {
        "mode": mode,
        "title": title,
        "date": datetime.now(timezone.utc).isoformat(),
        "lineup": lineup,
        "team_profile": team_profile,  # NEW field in the response
        "star_player": star,
    }
    return payload


def save_history(snapshot: dict) -> None:
    if not snapshot or not snapshot.get("lineup"):
        return
    if HISTORY_JSON.exists():
        try:
            data = json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
        except Exception:
            data = []
    else:
        data = []
    data.append(snapshot)
    HISTORY_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def read_history() -> list[dict]:
    if not HISTORY_JSON.exists():
        return []
    try:
        return json.loads(HISTORY_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
