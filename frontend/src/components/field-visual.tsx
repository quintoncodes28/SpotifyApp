// src/components/field-visual.tsx
"use client";
import * as React from "react";

/**
 * Sticker-style baseball diamond (transparent background).
 * Only the lines/diamond are drawn, so it looks like a cut-out.
 * The subtle glow uses --accent (green for Current, cyan for Legends).
 */
export default function FieldVisual() {
  const accent = "rgb(var(--accent))"; // theme tint

  return (
    <div className="relative w-full aspect-square">
      <svg
        viewBox="0 0 1000 1000"
        className="absolute inset-0 h-full w-full"
        aria-hidden
      >
        {/* Everything is transparent except these strokes */}
        <g
          fill="none"
          stroke="white"
          strokeLinecap="round"
          strokeLinejoin="round"
          // soft colored glow behind white strokes
          style={{ filter: `drop-shadow(0 0 8px ${accent})` }}
        >
          {/* ===== Diamond (home -> 1B -> 2B -> 3B -> home) ===== */}
          {/* Anchor points (rough MLB proportions within 1000x1000 viewBox): */}
          {/* Home(500,850), 1B(700,650), 2B(500,450), 3B(300,650) */}
          <polyline
            points="500,850 700,650 500,450 300,650 500,850"
            strokeWidth={14}
          />

          {/* ===== Baselines emphasized (same as diamond for clarity) ===== */}
          <line x1="500" y1="850" x2="700" y2="650" strokeWidth={14} />
          <line x1="700" y1="650" x2="500" y2="450" strokeWidth={14} />
          <line x1="500" y1="450" x2="300" y2="650" strokeWidth={14} />
          <line x1="300" y1="650" x2="500" y2="850" strokeWidth={14} />

          {/* ===== Foul lines from home plate out to edges ===== */}
          {/* Extend along the home->3B and home->1B vectors */}
          <line x1="480" y1="830" x2="60" y2="420" strokeWidth={10} />
          <line x1="520" y1="830" x2="940" y2="420" strokeWidth={10} />

	  {/* ===== NEW: Outfield arc connecting foul-line tips ===== */}
          {/* Adjust the control point (500,180) higher/lower to change curve */}
          <path
            d="M60,420 Q500,-155 940,420"
            strokeWidth={10}
          />

          {/* ===== Bases (little diamonds) ===== */}
          <rect
            x="488"
            y="438"
            width="24"
            height="24"
            transform="rotate(45 500 450)"
            strokeWidth={8}
          />
          <rect
            x="688"
            y="638"
            width="24"
            height="24"
            transform="rotate(45 700 650)"
            strokeWidth={8}
          />
          <rect
            x="288"
            y="638"
            width="24"
            height="24"
            transform="rotate(45 300 650)"
            strokeWidth={8}
          />

          {/* ===== Pitcher's mound ===== */}
          <line x1="480" y1="650" x2="520" y2="650" strokeWidth={8} />
        </g>
      </svg>
    </div>
  );
}
