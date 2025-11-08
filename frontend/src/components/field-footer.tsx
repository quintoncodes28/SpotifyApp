"use client";
import * as React from "react";

export default function FieldFooter({
  team,
  opponent,
  mode,
  starTitle,
  signedAtISO,
}: {
  team: string;
  opponent?: string;
  mode: "current" | "alltime";
  starTitle?: string;
  signedAtISO?: string;
}) {
  const accent = "rgb(var(--accent))";
  const dt = signedAtISO ? new Date(signedAtISO) : null;
  const dateStr = dt ? dt.toLocaleDateString() : "";
  const timeStr = dt ? dt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "";

  return (
    <div className="mt-5 rounded-2xl border border-white/10 overflow-hidden relative">
      {/* subtle background */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          background:
            "radial-gradient(120% 80% at 100% 0%, rgba(255,255,255,0.08), transparent 60%), radial-gradient(120% 80% at 0% 100%, rgba(255,255,255,0.06), transparent 60%)",
        }}
      />
      {/* accent stripe */}
      <div
        className="h-1 w-full"
        style={{ background: accent, boxShadow: `0 0 16px ${accent}` }}
      />

      <div className="relative p-4 flex flex-wrap items-center justify-between gap-4">
        {/* Left: matchup */}
        <div className="flex items-center gap-3">
          <div
            className="h-8 w-8 rounded-full"
            style={{ background: accent, boxShadow: `0 0 18px ${accent}` }}
          />
          <div className="leading-tight">
            <div className="text-xs opacity-60 uppercase tracking-wide">
              {mode === "current" ? "Current Lineup" : "Legends Lineup"}
            </div>
            <div className="text-base font-semibold">
              {team || "Your Team"} {opponent ? `vs ${opponent}` : ""}
            </div>
          </div>
        </div>

        {/* Middle: star track */}
        {starTitle ? (
          <div className="px-3 py-1 rounded-full bg-black/60 border border-white/10 text-sm">
            ⭐ Star track: <span className="font-medium">{starTitle}</span>
          </div>
        ) : (
          <div className="text-sm opacity-70">Pick your star player</div>
        )}

        {/* Right: time stamp */}
        <div className="text-right leading-tight">
          <div className="text-xs opacity-60 uppercase tracking-wide">Snapshot</div>
          <div className="text-sm">{dateStr} {timeStr}</div>
        </div>
      </div>
    </div>
  );
}
