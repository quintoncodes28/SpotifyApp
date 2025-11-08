"use client";
import * as React from "react";

type Item = {
  position: string;          // "CF","SS","RF","1B","2B","3B","C","LF","P"
  artist: string;
  title?: string;
  track_id?: string;
  album_cover?: string | null;
  artist_image?: string | null;
  // artist_image?: string | null; // (optional if you added it later)
};

export default function FieldPerspective({
  items,
  showLabels = true,
}: {
  items: Item[];
  showLabels?: boolean;
}) {
  const accent = "rgb(var(--accent))";

  // --- Key points (perspective) ---
  const H  = { x: 500, y: 590 }; // home
  const B1 = { x: 660, y: 500 }; // 1B
  const B2 = { x: 500, y: 410 }; // 2B
  const B3 = { x: 340, y: 500 }; // 3B
  const CENTER = { x: 500, y: 500 };

  // Helpers
  const mid = (a: { x: number; y: number }, b: { x: number; y: number }) => ({
    x: (a.x + b.x) / 2,
    y: (a.y + b.y) / 2,
  });
  const toward = (p: { x: number; y: number }, q: { x: number; y: number }, k: number) => ({
    x: p.x + (q.x - p.x) * k,
    y: p.y + (q.y - p.y) * k,
  });

  // ---- Concave infield path (quadratic Béziers) ----
  const k = 0.65; // curve depth 0.55–0.75
  const mH1 = mid(H, B1);
  const m12 = mid(B1, B2);
  const m23 = mid(B2, B3);
  const m3H = mid(B3, H);

  const cH1 = toward(mH1, CENTER, k);
  const c12 = toward(m12, CENTER, k);
  const c23 = toward(m23, CENTER, k);
  const c3H = toward(m3H, CENTER, k);

  const infieldPath = [
    `M ${H.x},${H.y}`,
    `Q ${cH1.x},${cH1.y} ${B1.x},${B1.y}`,
    `Q ${c12.x},${c12.y} ${B2.x},${B2.y}`,
    `Q ${c23.x},${c23.y} ${B3.x},${B3.y}`,
    `Q ${c3H.x},${c3H.y} ${H.x},${H.y}`,
  ].join(" ");

  // --- Bases: diamond points + rotation controls ---
  const BASE_SIZE = 14; // change to resize bases
  const BASE_ROT = {
    B1: -8, // deg (clockwise negative here for a slight lean)
    B2: 0,
    B3: 8,
  };
  const baseDiamond = (x: number, y: number, s: number) =>
    `${x},${y - s} ${x + s},${y} ${x},${y + s} ${x - s},${y}`;

  // Avatar layout
  const POS: Record<string, { x: number; y: number }> = {
    CF: { x: 50, y: 15 },
    LF: { x: 18, y: 22 },
    RF: { x: 82, y: 22 },
    "2B": { x: 58, y: 38 },
    SS: { x: 42, y: 38 },
    "3B": { x: 31, y: 50 },
    "1B": { x: 69, y: 50 },
    P:  { x: 50, y: 60 },
    C:  { x: 50, y: 76 },
  };

  const Marker = ({ it }: { it: Item }) => {
    const p = POS[it.position] ?? { x: 50, y: 50 };
    const href = it.track_id ? `https://open.spotify.com/track/${it.track_id}` : undefined;
    // before: const img = it.album_cover || null;
    const img = it.artist_image || it.album_cover || null;


    return (
      <a
        href={href}
        target="_blank"
        rel="noreferrer"
        style={{
          position: "absolute",
          left: `${p.x}%`,
          top: `${p.y}%`,
          transform: "translate(-50%, -50%)",
          textDecoration: "none",
        }}
      >
        <div className="flex flex-col items-center gap-1">
          <div
            className="h-16 w-16 rounded-full overflow-hidden ring-2 ring-white/80 shadow-md"
            style={{ filter: `drop-shadow(0 0 6px ${accent})` }}
            title={`${it.position} • ${it.artist}${it.title ? ` — ${it.title}` : ""}`}
          >
            {img ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={img} alt="" className="h-full w-full object-cover" />
            ) : (
              <div className="h-full w-full bg-white/20" />
            )}
          </div>
          {showLabels && (
            <div className="px-2 py-0.5 rounded-lg bg-black/65 border border-white/10 text-white text-xs whitespace-nowrap">
              <span className="opacity-70 mr-1">{it.position}</span>
              <span className="font-medium">{it.artist}</span>
            </div>
          )}
        </div>
      </a>
    );
  };

  return (
    <div className="relative w-full aspect-[1000/860]">
      <svg viewBox="0 0 1000 860" className="absolute inset-0 h-full w-full" aria-hidden>
        {/* Outfield fan */}
        <path d="M40,330 Q500,90 960,330 L560,620 L440,620 Z" fill={accent} opacity="0.20" />

        <g
          fill="none"
          stroke="white"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ filter: `drop-shadow(0 0 8px ${accent})` }}
        >
          {/* Foul lines */}
          <line x1="480" y1="590" x2="40" y2="330" strokeWidth={8} />
          <line x1="520" y1="590" x2="960" y2="330" strokeWidth={8} />

          {/* Outfield arc */}
          <path d="M40,330 Q500,100 960,330" strokeWidth={8} />

          {/* Mound */}
          <ellipse cx="500" cy="515" rx="38" ry="24" strokeWidth={8} />
          <line x1="485" y1="515" x2="515" y2="515" strokeWidth={6} />

          {/* Home plate outline */}
          <path d="M500,560 l-34,0 0,22 34,22 34,-22 0,-22 z" strokeWidth={8} />
        </g>

        {/* Filled, rotatable bases */}
        <g>
          {/* 2B */}
          <polygon
            points={baseDiamond(B2.x, B2.y, BASE_SIZE * 0.8)}
            fill="white"
            stroke="white"
            strokeWidth={4}
            transform={`rotate(${BASE_ROT.B2} ${B2.x} ${B2.y})`}
          />
          {/* 1B */}
          <polygon
            points={baseDiamond(B1.x - 40, B1.y, BASE_SIZE * 0.8)}
            fill="white"
            stroke="white"
            strokeWidth={4}
            transform={`rotate(${BASE_ROT.B2} ${B2.x} ${B2.y})`}
          />
          {/* 3B */}
          <polygon
            points={baseDiamond(B3.x + 40, B3.y, BASE_SIZE * 0.8)}
            fill="white"
            stroke="white"
            strokeWidth={4}
            transform={`rotate(${BASE_ROT.B2} ${B2.x} ${B2.y})`}
          />
        </g>
      </svg>

      {/* Markers */}
      {items.map((it) => (
        <Marker key={`${it.position}-${it.artist}`} it={it} />
      ))}
    </div>
  );
}
