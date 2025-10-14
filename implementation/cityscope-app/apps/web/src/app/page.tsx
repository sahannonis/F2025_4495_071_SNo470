"use client";
import { useEffect, useMemo, useState } from "react";
import { getNeighborhoods, getSummary, getCompare } from "@/lib/api";
import type { Neighborhood, Summary } from "@/lib/types";
import ScoreCards from "@/components/ScoreCards";
import CompareBar from "@/components/CompareBar";
import NeighborhoodMap from "@/components/NeighborhoodMap";

export default function HomePage() {
  const [neighborhoods, setNeighborhoods] = useState<Neighborhood[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [compareRows, setCompareRows] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getNeighborhoods()
      .then((data) => {
        setNeighborhoods(data);
        const defaults = data.slice(0, 3).map((n) => n.id);
        setSelectedIds(defaults);
        setActiveId(defaults[0] ?? null);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (activeId != null) {
      getSummary(activeId).then(setSummary).catch(() => setSummary(null));
    }
  }, [activeId]);

  useEffect(() => {
    if (!selectedIds.length) return;
    getCompare(selectedIds)
      .then((rows) => {
        const byId = new Map<number, any>();
        for (const row of rows) byId.set(row.neighborhoodId, row);
        const shaped = selectedIds.map((id) => {
          const n = neighborhoods.find((x) => x.id === id);
          const r = byId.get(id);
          return {
            name: n?.name || `#${id}`,
            avgRent: r?.avgRent ?? 0,
            transitCount: r?.transitCount ?? 0,
            mallCount: r?.mallCount ?? 0,
            score: r?.score ?? 0,
          };
        });
        setCompareRows(shaped);
      })
      .catch(() => setCompareRows([]));
  }, [selectedIds, neighborhoods]);

  const center = useMemo<[number, number]>(() => {
    if (!neighborhoods.length) return [49.2827, -123.1207];
    return [neighborhoods[0].centerLat, neighborhoods[0].centerLng];
  }, [neighborhoods]);

  function toggleSelect(id: number) {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  if (loading) return <div className="p-6">Loading…</div>;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl md:text-3xl font-bold">CityScope: Real Estate & Community Data Explorer</h1>
      <p className="text-gray-600 mt-1">Compare neighborhoods by affordability, transit, and amenities.</p>

      {/* Controls */}
      <div className="mt-4 flex flex-col md:flex-row gap-3 md:items-end">
        <div className="flex-1">
          <label className="text-sm text-gray-600">Neighborhood</label>
          <select
            className="w-full border rounded-lg p-2"
            value={activeId ?? ""}
            onChange={(e) => setActiveId(Number(e.target.value))}
          >
            {neighborhoods.map((n) => (
              <option key={n.id} value={n.id}>
                {n.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1">
          <label className="text-sm text-gray-600">Compare (multi-select)</label>
          <div className="flex flex-wrap gap-2 mt-2">
            {neighborhoods.map((n) => {
              const active = selectedIds.includes(n.id);
              return (
                <button
                  key={n.id}
                  onClick={() => toggleSelect(n.id)}
                  className={`px-3 py-1 rounded-full border ${
                    active ? "bg-black text-white" : "bg-white text-black"
                  }`}
                >
                  {n.name}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Map */}
      <div className="mt-5">
        <NeighborhoodMap
          center={center}
          items={neighborhoods.map((n) => ({
            id: n.id,
            name: n.name,
            centerLat: n.centerLat,
            centerLng: n.centerLng,
            score: n.snapshots?.[0]?.score ?? 0,
            onSelect: (id) => {
              setActiveId(id);
              if (!selectedIds.includes(id)) setSelectedIds((prev) => [...prev, id]);
            },
          }))}
        />
      </div>

      {/* Summary cards */}
      {summary && <ScoreCards summary={summary} />}

      {/* Compare bar */}
      <div className="mt-4">
        <CompareBar data={compareRows} />
      </div>
    </div>
  );
}
