"use client";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { useMemo } from "react";

const defaultIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
});

type Item = {
  id: number;
  name: string;
  centerLat: number;
  centerLng: number;
  score: number;
  onSelect?: (id: number) => void;
};

export default function NeighborhoodMap({ items, center }: { items: Item[]; center: [number, number] }) {
  const bounds = useMemo(() => {
    if (!items.length) return null;
    const latlngs = items.map((i) => [i.centerLat, i.centerLng]) as [number, number][];
    return L.latLngBounds(latlngs);
  }, [items]);

  return (
    <div className="rounded-xl overflow-hidden border h-96">
      <MapContainer 
        {...(bounds ? { bounds } : { center, zoom: 12 })}
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        {items.map((n) => (
          <Marker
            position={[n.centerLat, n.centerLng]}
            key={n.id}
            eventHandlers={{ click: () => n.onSelect?.(n.id) }}
          >
            <Popup>
              <div className="font-semibold">{n.name}</div>
              <div className="text-sm">Score: {n.score}</div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
