"use client";
import * as React from "react";

type Entry = {
  position: string;
  title: string;
  artist: string;
  score?: number;
  track_id?: string;
  album_cover?: string | null;
};

export default function LineupCard({
  team = "Spotify Lineup",
  opponent = "",
  date = new Date().toLocaleDateString(),
  time = "",
  field,                         // if not passed, we’ll default to `${team} Park`
  homeAway = "HOME",
  lineup,
  starTitle,
}: {
  team?: string;
  opponent?: string;
  date?: string;
  time?: string;
  field?: string;
  homeAway?: "HOME" | "VISITOR";
  lineup: Entry[];
  starTitle?: string | null;
}) {
  const rows = lineup.slice(0, 9);
  const fieldName = field || `${team} Park`;

  return (
    <div
      className="w-full rounded-2xl bg-[rgb(var(--card))] text-[rgb(var(--text))] border border-white/10 shadow-2xl"
      style={{ /* allow it to comfortably fill half the page */ minHeight: 640 }}
    >
      {/* Header */}
      <div className="px-5 pt-5">
        <div className="text-center">
          <div className="text-[28px] font-extrabold tracking-wide">
            OFFICIAL LINE-UP
          </div>
        </div>

        {/* Meta grid */}
        <div className="mt-4 grid grid-cols-2 gap-3 text-[12px]">
          <Meta label="TEAM:" value={team} />
          <Meta label="DATE:" value={date} />
          <Meta label="OPP:"  value={opponent} />
          <Meta label="TIME:" value={time} />
          <Meta label="FIELD:" value={fieldName} />
          <div className="flex items-center gap-3">
            <span className="w-16 text-white/60">HOME:</span>
            <Dot checked={homeAway === "HOME"} />
            <span className="w-16 text-white/60 text-right">VISITOR:</span>
            <Dot checked={homeAway === "VISITOR"} />
          </div>
        </div>
      </div>

      {/* Table header */}
      <div className="mt-4 border-t border-white/10" />
      <div className="grid grid-cols-[44px_1fr_60px_110px] text-[12px] font-semibold text-white/80">
        <Cell head>#</Cell>
        <Cell head>STARTING PLAYER</Cell>
        <Cell head center>POS</Cell>
        <Cell head>SUBSTITUTION</Cell>
      </div>

      {/* Rows */}
      <div className="border-t border-white/10">
        {Array.from({ length: 9 }).map((_, i) => {
          const row = rows[i];
          const isStar = row && starTitle && row.title === starTitle;
          const href = row?.track_id ? `https://open.spotify.com/track/${row.track_id}` : undefined;

          return (
            <div
              key={i}
              className="grid grid-cols-[44px_1fr_60px_110px] text-[13px] border-b border-white/10"
              style={{ minHeight: 56 }}
            >
              <Cell border className="tabular-nums">{i + 1}</Cell>

              <Cell border>
                {row ? (
                  <a
                    href={href}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-3 hover:bg-white/5 rounded-lg -mx-1 px-1 py-1.5 transition"
                    title={href ? "Open in Spotify" : undefined}
                  >
                    {/* album cover */}
                    {row.album_cover ? (
                      <img
                        src={row.album_cover}
                        alt=""
                        className="h-9 w-9 rounded-md object-cover border border-white/10"
                      />
                    ) : (
                      <div className="h-9 w-9 rounded-md border border-white/10 bg-white/5" />
                    )}

                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        {isStar && (
                          <span
                            className="inline-flex h-2.5 w-2.5 rounded-full"
                            style={{ background: "rgb(var(--accent))" }}
                            title="Star Player"
                          />
                        )}
                        <span className="font-medium truncate">{row.title}</span>
                      </div>
                      <div className="opacity-70 truncate">— {row.artist}</div>
                    </div>
                  </a>
                ) : (
                  <span className="opacity-40">—</span>
                )}
              </Cell>

              <Cell border center className="font-semibold">
                {row?.position ?? ""}
              </Cell>

              <Cell className="text-right text-[12px] tabular-nums text-white/70">
                {row?.score != null ? `HI ${Math.round(row.score * 100) / 100}` : ""}
              </Cell>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-5 py-2 text-[12px] text-white/70 flex items-center gap-2">
        COACH:
        <div className="flex-1 border-b border-white/10" />
        <span className="text-[rgb(var(--accent))]">UMPIRE COPY</span>
      </div>
    </div>
  );
}

function Meta({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="w-16 text-white/60">{label}</span>
      <div className="flex-1 h-7 px-2 rounded-md bg-white/[0.03] border border-white/10 flex items-center overflow-hidden">
        <span className="truncate">{value ?? ""}</span>
      </div>
    </div>
  );
}

function Dot({ checked }: { checked: boolean }) {
  return (
    <div
      className={`h-3 w-3 rounded-full border ${
        checked ? "border-[rgb(var(--accent))] bg-[rgb(var(--accent))]" : "border-white/30"
      }`}
    />
  );
}

function Cell({
  children,
  border,
  center,
  head,
  className = "",
}: {
  children: React.ReactNode;
  border?: boolean;
  center?: boolean;
  head?: boolean;
  className?: string;
}) {
  const cls =
    (border ? "border-r border-white/10 " : "") +
    (center ? "text-center " : "") +
    (head ? "px-3 py-2 " : "px-3 py-2 ") +
    className;
  return <div className={cls}>{children}</div>;
}
