"use client";

import { useEffect, useMemo, useState } from "react";
import type { Neighborhood, Summary } from "@/lib/types";
import { getNeighborhoods, getSummary, getCompare, getStopsOverlay, getMallsOverlay } from "@/lib/api";
import ScoreCards from "@/components/ScoreCards";
import CompareBar from "@/components/CompareBar";
import MapWrapper from "@/components/MapWrapper";

type CompareRow = { name: string; avgRent: number; transitCount: number; mallCount: number; score: number };

export default function HomePage() {
  const [neighborhoods, setNeighborhoods] = useState<Neighborhood[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [activeId, setActiveId] = useState<number | null>(null);

  const [summary, setSummary] = useState<Summary | null>(null);
  const [compareRows, setCompareRows] = useState<CompareRow[]>([]);
  const [loading, setLoading] = useState(true);

  // Overlays
  const [showStops, setShowStops] = useState(false);
  const [showMalls, setShowMalls] = useState(false);
  const [stops, setStops] = useState<any[]>([]);
  const [malls, setMalls] = useState<any[]>([]);

  // Initial load of neighborhoods
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

  // Load summary for active neighborhood
  useEffect(() => {
    if (activeId == null) return;
    getSummary(activeId).then(setSummary).catch(() => setSummary(null));
  }, [activeId]);

  // Load comparison rows for selected neighborhoods
  useEffect(() => {
    if (!selectedIds.length || neighborhoods.length === 0) return;
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

  // Load overlays when active neighborhood or toggles change
  useEffect(() => {
    if (!activeId) return;
    
    console.log('Loading overlays for neighborhood:', activeId, { showStops, showMalls });
    
    if (showStops) {
      getStopsOverlay(activeId)
        .then((data) => {
          console.log('Stops loaded:', data.length, 'items');
          setStops(data);
        })
        .catch((error) => {
          console.error('Failed to load stops:', error);
          setStops([]);
        });
    } else {
      setStops([]);
    }
    
    if (showMalls) {
      getMallsOverlay(activeId)
        .then((data) => {
          console.log('Malls loaded:', data.length, 'items');
          setMalls(data);
        })
        .catch((error) => {
          console.error('Failed to load malls:', error);
          setMalls([]);
        });
    } else {
      setMalls([]);
    }
  }, [activeId, showStops, showMalls]);

  // Map center
  const center = useMemo<[number, number]>(() => {
    if (!neighborhoods.length) return [49.2827, -123.1207]; // default: Vancouver-ish
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
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        {/* Active neighborhood selector */}
        <div>
          <label className="text-sm text-gray-600">Neighborhood</label>
          <select
            className="mt-2 w-full border rounded-lg p-2"
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

        {/* Compare multi-select */}
        <div>
          <label className="text-sm text-gray-600">Compare (multi-select)</label>
          <div className="flex flex-wrap gap-2 mt-2">
            {neighborhoods.map((n) => {
              const active = selectedIds.includes(n.id);
              return (
                <button
                  key={n.id}
                  onClick={() => toggleSelect(n.id)}
                  className={`px-3 py-1 rounded-full border transition ${
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

      {/* Overlay toggles */}
      <div className="mt-3 flex flex-wrap gap-6 items-center">
        <label className="inline-flex items-center gap-2 text-sm">
          <input type="checkbox" checked={showStops} onChange={(e) => setShowStops(e.target.checked)} />
          Show stops {showStops && <span className="text-blue-600">({stops.length} loaded)</span>}
        </label>
        <label className="inline-flex items-center gap-2 text-sm">
          <input type="checkbox" checked={showMalls} onChange={(e) => setShowMalls(e.target.checked)} />
          Show malls {showMalls && <span className="text-red-600">({malls.length} loaded)</span>}
        </label>
      </div>

      {/* Map */}
      <div className="mt-5">
        <MapWrapper
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
          stops={stops}
          malls={malls}
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
