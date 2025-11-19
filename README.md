# Lineuptify – Spotify Lineup Web App 

Lineuptify turns your Spotify listening history into a **9-player baseball lineup**.

It pulls your recent plays, scores each track with a custom “HIv2” index, and places songs into field positions based on performance — like a sabermetrics view of your music.

---

##  Live Demo

Frontend (Next.js on Vercel):  
**https://spotify-app-six-nu.vercel.app**

Backend (FastAPI on Render):  
**https://lineuptify.onrender.com/healthz**

> Note: The app is currently configured as a **single-user demo** (my Spotify account).  
> It is portfolio-ready but not a public multi-user SaaS.

---

##  Tech Stack

### **Frontend**
- Next.js (App Router, TypeScript)
- React hooks
- ShadCN UI components
- Custom baseball field + lineup card rendering
- Deployed on Vercel

### **Backend**
- FastAPI (Python)
- Spotipy (Spotify API)
- SQLite (analytics & history storage)
- Custom ingestion script (`logger_recent.py`)
- Deployed on Render

---

##  How It Works

### 1. **Spotify Login (OAuth)**
1. User clicks **Sign in with Spotify**
2. Redirects to Spotify's login page
3. Spotify sends user back to `/callback` with an authorization code
4. The backend exchanges the code for tokens

### 2. **Data Ingestion (`logger_recent.py`)**
Fetches & stores:
- recently played tracks  
- artists  
- albums  
- track → artist mappings  
- saved-track flags  

Writes everything into **SQLite (`data.db`)**.

### 3. **HIv2 Scoring**
Weighted index using:
- 30-day play count (35%)
- 7-day momentum (20%)
- track popularity (15%)
- artist clout (10%)
- recency (10%)
- saved-track affinity (7%)
- diversity (3%)

Creates one score per track.

### 4. **Lineup Builder**
Assigns top-scoring tracks to baseball positions:
- CF, LF, RF  
- SS, 2B, 3B, 1B  
- C, P  

Returns:
- lineup[]
- star player
- team profile metadata
- snapshot timestamp

### 5. **Frontend Visualization**
- Baseball-style lineup card
- Actual baseball field with player avatars
- Current vs Legends mode
- Refresh button (reruns logger)

---

##  Environment Variables

Environment variables are **not committed**.  
Below are example templates:

### **Backend — `.env.example`**
```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_SCOPE=user-read-recently-played user-library-read user-top-read
SPOTIPY_REDIRECT_URI=https://lineuptify.onrender.com/callback
FRONTEND_URL=https://spotify-app-six-nu.vercel.app
```

### **Frontend — `.env.local.example`**
```env
NEXT_PUBLIC_API_BASE=https://lineuptify.onrender.com
```

---

##  Local Development

### Backend
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open:  
http://localhost:3000

---

## Status / Future Work

-  Full-stack working demo  
-  Currently single-user only  
-  Future upgrade: multi-user with per-user DB  
-  Future UI upgrades: animations, sharing, stats dashboard  
-  Possible mobile version  

---

## About the Me

Built by **Quinton Sterling** —  
Student athlete, data/tech builder, and future MLB analytics engineer.  
Focused on creating clean, production-quality projects that blend:  
**data, sports, and modern software engineering**.

---

## If you like this project…
Give the repo a star on GitHub :)  

