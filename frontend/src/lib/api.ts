// src/lib/api.ts
export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export type Mode = "current" | "alltime";

export async function getLineup(mode: Mode) {
  const res = await fetch(`${API_BASE}/lineup/${mode}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Failed to load lineup: ${res.status}`);
  return res.json() as Promise<{
    mode: Mode;
    title: string;
    date: string;
    lineup: Array<{
      title: string;
      artist: string;
      position: string;
      score: number;
      popularity: number;
      track_id: string;
      album_cover?: string | null;
    }>;
    star_player: { title: string } | null;
  }>;
}
