# backend/main.py
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pathlib import Path
import subprocess, sys, os
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

# ---------------- App & env ----------------
app = FastAPI(title="Spotify Sabermetrics API", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")  # .env next to main.py

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ---------------- CORS ----------------
allowlist = {FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in allowlist if o],
    allow_origin_regex=r"https://.*\.vercel\.app$",  # ✅ allow Vercel preview domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Startup debug ----------------
@app.on_event("startup")
def _startup_debug():
    here = BASE_DIR
    print(f"[DEBUG] CWD={Path.cwd()}")
    print(f"[DEBUG] __file__ dir={here}")
    try:
        listing = sorted(p.name for p in here.iterdir())
        print(f"[DEBUG] here list={listing}")
    except Exception as e:
        print(f"[DEBUG] list(dir) failed: {e}")

    # probe lineup_core but don't crash if missing deps
    try:
        import importlib
        importlib.import_module("lineup_core")
        print("[DEBUG] lineup_core import OK")
    except Exception as e:
        print(f"[DEBUG] lineup_core import FAILED: {type(e).__name__}: {e}")

# ---------------- Health ----------------
@app.get("/health")
def health():
    return {"ok": True}

@app.get("/healthz")
def healthz():
    return {"ok": True}

# ---------------- OAuth helpers ----------------
def get_oauth() -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8000/callback"),
        scope=os.getenv(
            "SPOTIPY_SCOPE",
            "user-read-recently-played user-library-read user-top-read",
        ),
        open_browser=False,
        cache_path=str(BASE_DIR / ".spotipy-cache"),
        show_dialog=False,
        requests_timeout=30,
    )

# ---------------- Logger runner ----------------
LOGGER = BASE_DIR / "logger_recent.py"
RUN_LOGGER_ON_LINEUP = True  # set False if you want to disable auto-logger

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
            timeout=180,
            check=True,
        )
        return {"ok": True, "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "stdout": e.stdout, "stderr": e.stderr}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "stdout": e.stdout or "", "stderr": f"Timeout: {e}"}

# ---------------- OAuth routes ----------------
@app.get("/login")
def login():
    oauth = get_oauth()
    auth_url = oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(request: Request, code: str = Query(...)):
    oauth = get_oauth()
    try:
        try:
            oauth.get_access_token(code)  # older spotipy
        except TypeError:
            oauth.get_access_token(code=code, check_cache=False)  # newer spotipy
    except Exception:
        return RedirectResponse(f"{FRONTEND_URL}?spotify_error=1")
    return RedirectResponse(f"{FRONTEND_URL}?connected=1")

@app.get("/debug-oauth")
def debug_oauth():
    oauth = get_oauth()
    return {
        "client_id_prefix": (os.getenv("SPOTIPY_CLIENT_ID") or "")[:8],
        "redirect_uri_env": os.getenv("SPOTIPY_REDIRECT_URI"),
        "redirect_uri_used": oauth.redirect_uri,
        "auth_url": oauth.get_authorize_url(),
    }

@app.get("/login_dry")
def login_dry():
    oauth = get_oauth()
    return {"auth_url": oauth.get_authorize_url()}

# ---------------- Lazy import core ----------------
def _lc():
    """Import lineup_core on demand so missing deps don't crash startup."""
    import importlib
    return importlib.import_module("lineup_core")

# ---------------- Core API ----------------
@app.post("/refresh")
def refresh():
    lc = _lc()
    result = run_logger()
    snap = lc.build_lineup(mode="current")
    if snap.get("lineup"):
        lc.save_history(snap)
    return JSONResponse({"refresh": result, "snapshot": snap})

@app.get("/lineup/current")
def lineup_current():
    lc = _lc()
    if RUN_LOGGER_ON_LINEUP:
        _ = run_logger()
    snap = lc.build_lineup(mode="current")
    if snap.get("lineup"):
        lc.save_history(snap)
    return snap

@app.get("/lineup/alltime")
def lineup_alltime():
    lc = _lc()
    if RUN_LOGGER_ON_LINEUP:
        _ = run_logger()
    snap = lc.build_lineup(mode="alltime")
    if snap.get("lineup"):
        lc.save_history(snap)
    return snap

@app.get("/history")
def history():
    lc = _lc()
    return {"history": lc.read_history()}
