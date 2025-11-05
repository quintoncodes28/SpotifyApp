# backend/refresh_runner.py
from __future__ import annotations
import sys, subprocess, sqlite3, os
from pathlib import Path
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
DB_PATH = (HERE / "data.db").resolve()
LOGGER_PATH = (HERE / "logger_recent.py").resolve()

def _iso_mtime(p: Path):
    return datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).isoformat() if p.exists() else None

def _count(conn, table):
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:
        return -1

def run():
    before_mtime = _iso_mtime(DB_PATH)
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as c:
            before_plays = _count(c, "plays")
    else:
        before_plays = -1

    if not LOGGER_PATH.exists():
        return {"ok": False, "error": f"logger_recent.py not found at {LOGGER_PATH}", "db_path": str(DB_PATH)}

    # Run the logger with the SAME Python/venv as FastAPI
    cmd = [sys.executable, str(LOGGER_PATH)]
    proc = subprocess.run(cmd, cwd=str(HERE), capture_output=True, text=True, env=os.environ.copy())

    after_mtime = _iso_mtime(DB_PATH)
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as c:
            after_plays = _count(c, "plays")
    else:
        after_plays = -1

    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "db_path": str(DB_PATH),
        "logger_path": str(LOGGER_PATH),
        "db_before": {"mtime_iso": before_mtime, "plays": before_plays},
        "db_after":  {"mtime_iso": after_mtime,  "plays": after_plays},
        "stdout": proc.stdout[-6000:],  # trimmed
        "stderr": proc.stderr[-6000:],
    }

if __name__ == "__main__":
    import json
    print(json.dumps(run(), indent=2))
