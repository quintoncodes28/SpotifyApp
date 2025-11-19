# backend/main.py
from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from pathlib import Path
import subprocess, sys, os, shutil, json
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify  # ✅ NEW

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
    allow_origin_regex=r"https://.*\.vercel\.app$",  # allow vercel previews
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- Helpers (per-user cache) ----------------
def cache_path_for(uid: str | None) -> str | None:
    if not uid:
        # fallback to env (optional) or default file
        return os.getenv("SPOTIPY_CACHE_PATH") or str(BASE_DIR / ".spotipy-cache")
    return str(BASE_DIR / f".spotipy-cache-{uid}")

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
def get_oauth(uid: str | None = None) -> SpotifyOAuth:
    return SpotifyOAuth(
        client_id=os.getenv("SPOTIPY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI", "http://localhost:8000/callback"),
        scope=os.getenv(
            "SPOTIPY_SCOPE",
            "user-read-recently-played user-library-read user-top-read",
        ),
        open_browser=False,
        cache_path=cache_path_for(uid),  # ✅ per-user cache
        show_dialog=False,
        requests_timeout=30,
    )

# ---------------- Logger runner ----------------
LOGGER = BASE_DIR / "logger_recent.py"
RUN_LOGGER_ON_LINEUP = True  # set False to disable auto-logger

def run_logger(uid: str | None):
    """Run logger_recent.py with per-user cache path via env."""
    if not LOGGER.exists():
        return {"ok": False, "note": f"{LOGGER.name} not found", "stdout": "", "stderr": ""}
    try:
        env = os.environ.copy()
        env["SPOTIPY_CACHE_PATH"] = cache_path_for(uid) or ""
        proc = subprocess.run(
            [sys.executable, str(LOGGER)],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            timeout=180,
            check=True,
            env=env,  # ✅ pass per-user cache path
        )
        return {"ok": True, "stdout": proc.stdout, "stderr": proc.stderr}
    except subprocess.CalledProcessError as e:
        return {"ok": False, "stdout": e.stdout, "stderr": e.stderr}
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "stdout": e.stdout or "", "stderr": f"Timeout: {e}"}

# ---------------- OAuth routes ----------------
@app.get("/login")
def login(request: Request):
    uid = request.cookies.get("uid")  # optional repeat visitor
    oauth = get_oauth(uid)
    return RedirectResponse(oauth.get_authorize_url())

@app.get("/callback")
def callback(request: Request, code: str = Query(...)):
    """
    Exchange code using default cache, discover the user's Spotify id,
    then move the token file into a per-user cache and set a cookie.
    """
    # Step 1: exchange code with temporary/default cache
    oauth0 = get_oauth(uid=None)
    try:
        try:
            token_info = oauth0.get_access_token(code)  # older spotipy
        except TypeError:
            token_info = oauth0.get_access_token(code=code, check_cache=False)  # newer
    except Exception:
        return RedirectResponse(f"{FRONTEND_URL}?spotify_error=1")

    # Step 2: find the user's Spotify id
    sp = Spotify(auth=token_info["access_token"])
    me = sp.me()
    uid = me.get("id")

    # Step 3: move cache file to a per-user path
    try:
        src = Path(cache_path_for(None))
        dst = Path(cache_path_for(uid))
        if src.exists():
            dst.write_text(src.read_text())
            src.unlink(missing_ok=True)
    except Exception as e:
        print(f"[WARN] cache move failed: {e}")

    # Step 4: set uid cookie and bounce to frontend
    resp = RedirectResponse(f"{FRONTEND_URL}?connected=1")
    # HttpOnly so JS can't read it; Lax so OAuth redirect keeps it
    resp.set_cookie("uid", uid or "", httponly=True, samesite="lax", max_age=60*60*24*30)
    return resp

@app.get("/debug-oauth")
def debug_oauth(request: Request):
    uid = request.cookies.get("uid")
    oauth = get_oauth(uid)
    return {
        "client_id_prefix": (os.getenv("SPOTIPY_CLIENT_ID") or "")[:8],
        "redirect_uri_env": os.getenv("SPOTIPY_REDIRECT_URI"),
        "redirect_uri_used": oauth.redirect_uri,
        "cache_path": oauth.cache_path,
        "auth_url": oauth.get_authorize_url(),
        "uid_cookie": uid,
    }

@app.get("/login_dry")
def login_dry(request: Request):
    uid = request.cookies.get("uid")
    return {"auth_url": get_oauth(uid).get_authorize_url()}

# ---------------- Lazy import core ----------------
def _lc():
    import importlib
    return importlib.import_module("lineup_core")

# ---------------- Core API ----------------
@app.post("/refresh")
def refresh(request: Request):
    uid = request.cookies.get("uid")
    lc = _lc()
    result = run_logger(uid)
    snap = lc.build_lineup(mode="current")
    if snap.get("lineup"):
        lc.save_history(snap)
    return JSONResponse({"refresh": result, "snapshot": snap})

@app.get("/lineup/current")
def lineup_current(request: Request):
    uid = request.cookies.get("uid")
    lc = _lc()
    if RUN_LOGGER_ON_LINEUP:
        _ = run_logger(uid)
    snap = lc.build_lineup(mode="current")
    if snap.get("lineup"):
        lc.save_history(snap)
    return snap

@app.get("/lineup/alltime")
def lineup_alltime(request: Request):
    uid = request.cookies.get("uid")
    lc = _lc()
    if RUN_LOGGER_ON_LINEUP:
        _ = run_logger(uid)
    snap = lc.build_lineup(mode="alltime")
    if snap.get("lineup"):
        lc.save_history(snap)
    return snap

@app.get("/history")
def history(request: Request):
    lc = _lc()
    return {"history": lc.read_history()}
