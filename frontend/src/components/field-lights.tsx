"use client";
import * as React from "react";

export default function FieldLights() {
  const accent = "rgb(var(--accent))";
  return (
    <div className="mt-5 relative overflow-hidden rounded-2xl border border-white/10">
      {/* dark base */}
      <div className="h-24 w-full bg-black/60" />

      {/* glow beams */}
      <div
        className="pointer-events-none absolute inset-0 opacity-70"
        style={{
          background: `
            radial-gradient(60% 140% at 20% -20%, ${accent}, transparent 60%),
            radial-gradient(60% 140% at 80% -20%, ${accent}, transparent 60%)
          `,
          filter: "blur(6px)",
          mixBlendMode: "screen",
        }}
      />

      {/* bulb rows */}
      <div className="pointer-events-none absolute top-2 left-1/2 -translate-x-1/2 flex gap-10">
        {[0,1].map((row) => (
          <div key={row} className="flex gap-1.5">
            {Array.from({ length: 18 }).map((_, i) => (
              <span
                key={i}
                className="inline-block h-1.5 w-1.5 rounded-full"
                style={{
                  background: "white",
                  boxShadow: "0 0 8px white, 0 0 20px white",
                  opacity: 0.9 - (Math.random() * 0.15),
                  transform: `translateY(${row * 8}px)`,
                }}
              />
            ))}
          </div>
        ))}
      </div>

      {/* top accent strip */}
      <div
        className="absolute top-0 left-0 right-0 h-0.5"
        style={{ background: accent, boxShadow: `0 0 16px ${accent}` }}
      />
    </div>
  );
}
