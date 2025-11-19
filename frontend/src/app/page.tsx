// src/app/page.tsx
"use client";

import * as React from "react";
import LineupCard from "@/components/lineup-card";
import FieldPerspective from "@/components/field-perspective";
import FieldFooter from "@/components/field-footer";
import dynamic from "next/dynamic";
const FieldLights = dynamic(() => import("@/components/field-lights"), { ssr: false });

type Mode = "current" | "alltime";
// 🔧 use your backend host/port by default
const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:1234";

React.useEffect(() => {
  fetch(`${API_BASE}/healthz`, { cache: "no-store" }).catch(() => {});
}, []);

// wake the backend so /login is instant
React.useEffect(() => {
  fetch(`${API_BASE}/healthz`, { cache: "no-store" }).catch(() => {});
}, []);

async function fetchLineup(mode: Mode) {
  const res = await fetch(`${API_BASE}/lineup/${mode}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load lineup: ${res.status}`);
  return res.json();
}
async function refreshBackend() {
  const res = await fetch(`${API_BASE}/refresh`, { method: "POST" });
  if (!res.ok) throw new Error("refresh failed");
  return res.json(); // { refresh: {...}, snapshot: {...} }
}

const COORDS: Record<string, { top: string; left: string }> = {
  CF: { top: "27%", left: "50%" },
  LF: { top: "40%", left: "22%" },
  RF: { top: "20%", left: "78%" },
  SS: { top: "47%", left: "36%" },
  "2B": { top: "47%", left: "64%" },
  "3B": { top: "60%", left: "30%" },
  "1B": { top: "60%", left: "70%" },
  C:  { top: "77%", left: "50%" },
  P:  { top: "60%", left: "50%" },
};

export default function Home() {
  const [mode, setMode] = React.useState<Mode>("current");
  const [team, setTeam] = React.useState<string>("Quinton");
  const [opp, setOpp] = React.useState<string>("");
  const [showPlayers, setShowPlayers] = React.useState<boolean>(true);

  const [data, setData] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(true);

  // Intro/login state
  const [connected, setConnected] = React.useState<boolean>(false);

  // tracks whether we've already done the first connected-run refresh
  const didInit = React.useRef(false);

  // Load "connected" from URL (?connected=1) OR localStorage on mount
  React.useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("connected") === "1") {
      window.localStorage.setItem("spotify_connected", "1");
      window.history.replaceState({}, "", window.location.pathname);
    }
    const saved = window.localStorage.getItem("spotify_connected");
    if (saved === "1") setConnected(true);
  }, []);

  // Persist "connected" so returning users skip intro
  React.useEffect(() => {
    if (connected) {
      window.localStorage.setItem("spotify_connected", "1");
    }
  }, [connected]);

  React.useEffect(() => {
    document.documentElement.setAttribute(
      "data-design",
      mode === "current" ? "current" : "legends"
    );
  }, [mode]);

  // First time after "connected": run /refresh (logger) then show snapshot.
  // Subsequent mode changes: just fetch that mode's lineup.
  React.useEffect(() => {
    if (!connected) return; // don't fetch until user connects

    let mounted = true;

    if (!didInit.current) {
      didInit.current = true;
      (async () => {
        try {
          setLoading(true);
          const body = await refreshBackend(); // runs logger_recent.py
          if (mounted && body?.snapshot && mode === "current") {
            setData(body.snapshot);
          } else {
            const d = await fetchLineup(mode);
            if (mounted) setData(d);
          }
        } catch (e) {
          console.error(e);
        } finally {
          if (mounted) setLoading(false);
        }
      })();
      return () => { mounted = false; };
    }

    // After first load (while connected): just fetch on mode change
    setLoading(true);
    fetchLineup(mode)
      .then((d) => mounted && setData(d))
      .finally(() => setLoading(false));

    return () => { mounted = false; };
  }, [mode, connected]);

  const starTitle = data?.star_player?.title;
  const signedAt = data?.date ? new Date(data.date) : undefined;
  const timeStr = signedAt
    ? signedAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    : "";

  // ---------- Intro screen ----------
  if (!connected) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-black text-white">
        <div className="max-w-lg w-full text-center space-y-6 px-6">
          <div className="space-y-2">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">Build your 9-song Lineup</h1>
            <p className="text-sm md:text-base opacity-80">
              Connect Spotify to generate a baseball-style starting nine from your listening history.
            </p>
          </div>

          <div className="rounded-2xl border border-white/15 bg-white/[0.04] p-5 text-left space-y-3">
            <ul className="text-sm opacity-85 list-disc pl-5 space-y-1">
              <li>We read your recently played tracks to compute HIv2.</li>
              <li>No posting, no DMs — just your lineup.</li>
              <li>You can disconnect anytime by clearing browser data.</li>
            </ul>
          </div>

          {/* Spotify-green Sign in button → backend /login */}
          <button
            onClick={() => {
              const base = (process.env.NEXT_PUBLIC_API_BASE ?? "http://127.0.0.1:1234").replace(/\/$/, "");
              window.location.assign(`${base}/login`);
            }}
            className="w-full md:w-auto inline-flex items-center justify-center px-5 py-3 rounded-2xl font-semibold
                       bg-[#1DB954] text-black hover:bg-[#1ed760] transition"
            aria-label="Sign in with Spotify"
          >
            Sign in
          </button>

          <p className="text-xs opacity-60">
            By continuing you agree to let the app read your recent plays to create the lineup.
          </p>
        </div>
      </main>
    );
  }

  // ---------- Main app (after connect) ----------
  return (
    <main className="mx-auto max-w-7xl lg:max-w-[1280px] px-4 py-6">
      {/* Header / controls */}
      <div className="mb-5 flex flex-wrap items-center gap-3 justify-between">
        <div className="text-sm opacity-70">{data?.title ?? "Spotify Lineup"}</div>

        <div className="flex items-center gap-3">
          {/* Team / Opponent inputs */}
          <div className="hidden md:flex items-center gap-2 text-sm">
            <label className="opacity-70">Team</label>
            <input
              value={team}
              onChange={(e) => setTeam(e.target.value)}
              placeholder="Your team"
              className="h-8 rounded-lg bg-white/[0.06] border border-white/15 px-2 outline-none"
            />
            <label className="ml-3 opacity-70">Opponent</label>
            <input
              value={opp}
              onChange={(e) => setOpp(e.target.value)}
              placeholder="Opponent"
              className="h-8 rounded-lg bg-white/[0.06] border border-white/15 px-2 outline-none"
            />
          </div>

          {/* HI explanation dropdown */}
          <details className="group relative">
            <summary className="cursor-pointer px-3 py-1.5 text-sm rounded-xl border border-white/15 hover:bg-white/5">
              HI index?
            </summary>
            <div className="absolute right-0 z-20 mt-2 w-[320px] rounded-xl border border-white/10 bg-black/90 p-3 text-sm leading-5">
              <div className="opacity-80">HIv2 = weighted z-scores:</div>
              <ul className="mt-2 list-disc pl-5 opacity-80 space-y-1">
                <li>Plays 30d (35%)</li>
                <li>Momentum: 7d − prev7d (20%)</li>
                <li>Track popularity (15%)</li>
                <li>Artist clout (10%)</li>
                <li>Recency (10%)</li>
                <li>Affinity/saved (7%)</li>
                <li>Diversity (3%)</li>
              </ul>
            </div>
          </details>

          {/* Toggle players */}
          <button
            onClick={() => setShowPlayers((v) => !v)}
            className="px-3 py-1.5 text-sm rounded-xl border border-white/15 hover:bg-white/5"
          >
            {showPlayers ? "Hide Players" : "Show Players"}
          </button>

          {/* Refresh lineup — use the snapshot returned by /refresh */}
          <button
            onClick={async () => {
              try {
                setLoading(true);
                const body = await refreshBackend();  // runs logger + builds CURRENT snapshot
                if (mode === "current" && body?.snapshot) {
                  setData(body.snapshot);             // no extra fetch needed
                } else {
                  const d = await fetchLineup(mode);  // for "alltime", fetch that view
                  setData(d);
                }
              } catch (e) {
                console.error(e);
                alert("Refresh failed. Check backend logs.");
              } finally {
                setLoading(false);
              }
            }}
            className="px-3 py-1.5 text-sm rounded-xl border border-white/15 hover:bg-white/5"
          >
            Refresh lineup
          </button>

          {/* Mode toggle */}
          <div className="inline-flex rounded-xl border border-white/15 overflow-hidden">
            <button
              onClick={() => setMode("current")}
              className={`px-3 py-1.5 text-sm ${mode === "current" ? "bg-white text-black" : "hover:bg-white/10"}`}
            >
              Current
            </button>
              <button
              onClick={() => setMode("alltime")}
              className={`px-3 py-1.5 text-sm ${mode === "alltime" ? "bg-white text-black" : "hover:bg-white/10"}`}
            >
              Legends
            </button>
          </div>
        </div>
      </div>

      {/* Two-column layout with a WIDER FIELD column */}
      <div className="grid grid-cols-1 md:grid-cols-[1.05fr_1.35fr] gap-6 items-start">
        {/* LEFT: Lineup Card */}
        <section className="flex justify-center md:justify-start">
          {loading ? (
            <div className="text-sm opacity-70">Loading lineup…</div>
          ) : !data?.lineup?.length ? (
            <div className="text-sm opacity-70">No lineup available.</div>
          ) : (
            <LineupCard
              team={team}
              opponent={opp}
              date={new Date().toLocaleDateString()}
              time={timeStr}
              homeAway="HOME"
              lineup={data.lineup.slice(0, 9).map((e: any) => ({
                position: e.position,
                title: e.title,
                artist: e.artist,
                score: e.score,
                track_id: e.track_id,
                album_cover: e.album_cover,
              }))}
              starTitle={starTitle}
            />
          )}
        </section>

        {/* RIGHT: Perspective field; avatars only when showPlayers is on */}
        <section className="sticky top-6">
          <FieldPerspective
            items={
              showPlayers
                ? (data?.lineup ?? []).slice(0, 9).map((e: any) => ({
                    position: e.position,
                    artist: e.artist,
                    title: e.title,
                    track_id: e.track_id,
                    album_cover: e.album_cover,
                    artist_image: e.artist_image,
                  }))
                : [] // hide players entirely
            }
            showLabels={showPlayers}
          />

          {/* Extras under the field */}
          <FieldLights />
          <FieldFooter
            team={team}
            opponent={opp}
            mode={mode}
            starTitle={starTitle}
            signedAtISO={data?.date}
          />

          {/* Team comparison label under the field */}
          {data?.team_profile?.label && (
            <div className="mt-4 flex justify-center">
              <span
                className="px-3 py-1.5 text-sm rounded-xl border bg-white/5"
                style={{
                  borderColor: "rgba(255,255,255,.12)",
                  boxShadow: "0 0 14px rgb(var(--accent))",
                }}
              >
                Team Profile: <span className="font-semibold">{data.team_profile.label}</span>
              </span>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
