"use client";
import { useDesignMode } from "@/components/design-mode";

export default function ModeToggle() {
  const { mode, setMode } = useDesignMode();
  return (
    <div className="inline-flex rounded-xl border border-white/15 overflow-hidden">
      <button
        onClick={() => setMode("current")}
        className={`px-3 py-1.5 text-sm ${mode==="current" ? "bg-white text-black" : "hover:bg-white/10"}`}
      >
        Current
      </button>
      <button
        onClick={() => setMode("legends")}
        className={`px-3 py-1.5 text-sm ${mode==="legends" ? "bg-white text-black" : "hover:bg-white/10"}`}
      >
        Legends
      </button>
    </div>
  );
}
