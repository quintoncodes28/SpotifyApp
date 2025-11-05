# backend/main.py
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from lineup_core import build_lineup, save_history, read_history
from pathlib import Path
import subprocess, sys, os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

app = FastAPI(title="Spotify Sabermetrics API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "https://your-frontend-ngrok-url.ngrok.io",
        "https://your-vercel-app.vercel.app",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
LOGGER = BASE_DIR / "logger_recent.py"

# Load env (.env lives next to main.py / logger_recent.py)
load_dotenv(BASE_DIR / ".env")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

def get_oauth() -> SpotifyOAuth:
    """
    Build a SpotifyOAuth that uses the SAME cache file as logger_recent.py
    so once the user authorizes via /login -> /callback, your /refresh
    and logger runs will succeed without hanging.
    """
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8000/callback"),
        scope=os.getenv(
            "SPOTIPY_SCOPE",
            "user-read-recently-played user-library-read user-top-read"
        ),
        open_browser=False,
        cache_path=str(BASE_DIR / ".spotipy-cache"),
        show_dialog=False,
        requests_timeout=30,
    )

# Set this True if you want the logger to run on every lineup request too
RUN_LOGGER_ON_LINEUP = True

def run_logger():
    """Run logger_recent.py with the current Python, block until it finishes."""
    if not LOGGER.exists():
        return {"ok": False, "note": f"{LOGGER.name} not found", "stdout": "", "stderr": ""}
    try:
        proc = subprocess.run(
            [sys.executable, str(LOGGER)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=180,   # 3 minutes
            check=True,
        )
        return {"ok": True, "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "stdout": e.stdout, "stderr": e.stderr}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "stdout": e.stdout or "", "stderr": f"Timeout: {e}"}

# ------------------ OAUTH REDIRECT FLOW ------------------

@app.get("/login")
def login():
    """
    Redirect the user to Spotify Accounts to approve access.
    After approval, Spotify will redirect to /callback with a code.
    """
    oauth = get_oauth()
    auth_url = oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(request: Request, code: str = Query(...)):
    """
    Spotify redirects here after the user approves. We exchange the code
    for tokens; SpotifyOAuth writes them to .spotipy-cache.
    Then we bounce the user back to the frontend with ?connected=1.
    """
    oauth = get_oauth()
    try:
        # Spotipy signature changed across versions; handle both
        try:
            oauth.get_access_token(code)  # older spotipy
        except TypeError:
            oauth.get_access_token(code=code, check_cache=False)  # newer spotipy
    except Exception:
        return RedirectResponse(f"{FRONTEND_URL}?spotify_error=1")
    return RedirectResponse(f"{FRONTEND_URL}?connected=1")

# ------------------ DEBUG ROUTES ------------------

@app.get("/debug-oauth")
def debug_oauth():
    """Inspect exactly what OAuth config and authorize URL are being used."""
    oauth = get_oauth()
    auth_url = oauth.get_authorize_url()
    return {
        "client_id_prefix": (os.getenv("SPOTIPY_CLIENT_ID") or "")[:8],
        "redirect_uri_env": os.getenv("SPOTIPY_REDIRECT_URI"),
        "redirect_uri_used": oauth.redirect_uri,
        "auth_url": auth_url,
    }

@app.get("/login_dry")
def login_dry():
    """Return the Spotify authorize URL without redirecting."""
    oauth = get_oauth()
    return {"auth_url": oauth.get_authorize_url()}

# ------------------ CORE API ------------------

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/refresh")
def refresh():
    """Manually trigger the logger, then return a fresh CURRENT snapshot."""
    result = run_logger()
    snap = build_lineup(mode="current")
    if snap.get("lineup"):
        save_history(snap)
    return JSONResponse({"refresh": result, "snapshot": snap})

@app.get("/lineup/current")
def lineup_current():
    if RUN_LOGGER_ON_LINEUP:
        _ = run_logger()
    snap = build_lineup(mode="current")
    if snap.get("lineup"):
        save_history(snap)
    return snap

@app.get("/lineup/alltime")
def lineup_alltime():
    if RUN_LOGGER_ON_LINEUP:
        _ = run_logger()
    snap = build_lineup(mode="alltime")
    if snap.get("lineup"):
        save_history(snap)
    return snap

@app.get("/history")
def history():
    return {"history": read_history()}
