"use client";
import { useTheme } from "next-themes";

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const isDark = theme !== "light"; // defaultTheme="dark"
  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="px-3 py-1.5 rounded-xl border border-white/20 hover:border-white/40"
      title={`Current: ${isDark ? "dark" : "light"}`}
    >
      Toggle {isDark ? "Light" : "Dark"}
    </button>
  );
}
