# Lineuptify – Spotify Lineup Web App ⚾🎧

Lineuptify turns your Spotify listening history into a **9-player baseball lineup**.

It pulls your recent plays, scores each track with a custom “HIv2” index, and places songs into field positions based on performance – like a sabermetrics view of your music.

---

## 🚀 Live Demo

Frontend (Next.js on Vercel):  
**https://spotify-app-six-nu.vercel.app**  

Backend (FastAPI on Render):  
**https://lineuptify.onrender.com/healthz** (basic health check)

> Note: The app is currently configured as a **single-user demo** (my Spotify account). It’s built to show full-stack skills, not as a SaaS product yet.

---

## 🧱 Tech Stack

**Frontend**
- Next.js (App Router, TypeScript)
- React hooks for state and effects
- Custom baseball field + lineup card visualization
- Deployed on Vercel

**Backend**
- FastAPI (Python)
- Spotipy (Spotify Web API)
- SQLite (local DB)
- Custom logger script (`logger_recent.py`) to ingest Spotify history
- Deployed on Render

---

## 🧠 How It Works

1. **Spotify Login (OAuth)**
   - User clicks “Sign in with Spotify”
   - Backend `/login` redirects to Spotify’s Accounts page
   - Spotify redirects back to `/callback` with an authorization code

2. **Data Ingestion (`logger_recent.py`)**
   - Uses Spotify API to fetch **recently played tracks**
   - Stores:
     - plays (timestamps, track ids)
     - tracks
     - artists
     - albums
     - track ↔ artist relationships
   - Writes everything into `data.db` (SQLite)

3. **Scoring / HIv2 Index**
   - A custom metric that considers:
     - plays in the last 30 days
     - momentum (7-day change)
     - track popularity
     - artist popularity
     - recency
     - whether you’ve saved the track
   - Produces a **score per track** used to rank songs

4. **Lineup Builder**
   - The backend chooses top tracks and maps them into:
     - CF, LF, RF, SS, 2B, 3B, 1B, C, P
   - Returns a JSON `lineup` array plus metadata:
     - team profile (e.g. “Star Studded”)
     - star player
     - snapshot timestamp

5. **Frontend Visualization**
   - Calls `/refresh` or `/lineup/current`
   - Renders:
     - a baseball lineup card (with HI scores)
     - a field view (players positioned on the field)
     - a footer with team name, opponent, mode (“Current” vs “Legends”)

---

## 🔐 Environment Variables

The real `.env` files are **not committed** for security.  
Here’s an example of what’s needed:

**Backend `.env.example`**

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_SCOPE=user-read-recently-played user-library-read user-top-read
SPOTIPY_REDIRECT_URI=https://lineuptify.onrender.com/callback
FRONTEND_URL=https://spotify-app-six-nu.vercel.app
