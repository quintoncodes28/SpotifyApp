# Lineuptify – Spotify Lineup Web App ⚾🎧

Lineuptify turns your Spotify listening history into a **9-player baseball lineup**.

It pulls your recent plays, scores each track with a custom “HIv2” index, and places songs into field positions based on performance – like a sabermetrics view of your music.

---

## 🚀 Live Demo

Frontend (Next.js on Vercel):  
**https://spotify-app-six-nu.vercel.app**

Backend (FastAPI on Render):  
**https://lineuptify.onrender.com/healthz**

> Note: The app is currently configured as a **single-user demo** (my Spotify account).  
> It is portfolio-ready but not a public multi-user SaaS.

---

## 🧱 Tech Stack

### **Frontend**
- Next.js (App Router, TypeScript)
- React (hooks + dynamic components)
- Custom baseball field + lineup card visualization
- TailwindCSS
- Deployed on Vercel

### **Backend**
- FastAPI (Python)
- Spotipy (Spotify Web API)
- SQLite (local DB)
- Custom ingestion script (`logger_recent.py`)
- Deployed on Render

---

## 🧠 How It Works

### 1. **Spotify Login (OAuth)**
- User clicks **Sign in with Spotify**
- Backend `/login` → redirects to Spotify Accounts
- Spotify redirects back to `/callback` with an auth code

### 2. **Data Ingestion (`logger_recent.py`)**
Fetches:
- recently played tracks  
- full track metadata  
- artist data (popularity, followers, genres)  
- album data  
- saved-track flags  

Then stores everything into `data.db`.

### 3. **HIv2 Scoring System**
Weighted model combining:
- 30-day play counts  
- 7-day momentum  
- track popularity  
- artist popularity  
- recency  
- saved-track affinity  
- diversity  

Produces a single “sabermetrics-style” score for each track.

### 4. **Lineup Builder**
Turns the highest scoring tracks into a baseball lineup:
- CF, LF, RF  
- SS, 2B, 3B, 1B  
- C, P  

Returns a JSON response that includes:
- lineup  
- star player  
- team profile  
- snapshot timestamp  

### 5. **Frontend Presentation**
- Dynamic lineup card  
- Baseball field player placement with icons  
- Star player highlight  
- “Current” vs “Legends” toggle  

---

## 🔐 Environment Variables

### **Backend – `.env.example`**

```env
SPOTIPY_CLIENT_ID=your_spotify_client_id
SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
SPOTIPY_SCOPE=user-read-recently-played user-library-read user-top-read
SPOTIPY_REDIRECT_URI=https://lineuptify.onrender.com/callback
FRONTEND_URL=https://spotify-app-six-nu.vercel.app
```

### **Frontend – `.env.local.example`**

```env
NEXT_PUBLIC_API_BASE=https://lineuptify.onrender.com
```

---

## 🧪 Local Development

### **Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### **Frontend**

```bash
cd frontend
npm install
npm run dev
```

---

## 📌 Status / Future Work

Current version:
- Fully functional **single-user full-stack demo**
- End-to-end OAuth + data ingestion + scoring + UI

Possible future improvements:
- Multi-user support with secure per-user data  
- Background ingestion (Celery, RQ, or cron workers)  
- User accounts with persistent profiles  
- Sharable lineup pages (e.g., `/u/username/lineup`)  
- Animated transitions + improved UI polish  
- Export lineup as an image  

---

## 👤 About the Developer

Built by **Quinton Sterling** —  
Baseball player, data/tech major, and full-stack builder.

If you’d like to connect:  
**https://www.linkedin.com/in/quinton-sterling/**

---
