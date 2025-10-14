import type { Neighborhood, Summary } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:4000";

export async function getNeighborhoods(): Promise<Neighborhood[]> {
  const res = await fetch(`${BASE}/neighborhoods`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch neighborhoods");
  return res.json();
}

export async function getSummary(id: number): Promise<Summary> {
  const res = await fetch(`${BASE}/neighborhoods/${id}/summary`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}

export async function getCompare(ids: number[]) {
  const q = ids.length ? `?ids=${ids.join(",")}` : "";
  const res = await fetch(`${BASE}/compare${q}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch comparison");
  return res.json();
}
