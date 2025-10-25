"use client";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import { useMemo, useEffect } from "react";

type Item = {
  id: number;
  name: string;
  centerLat: number;
  centerLng: number;
  score: number;
  onSelect?: (id: number) => void;
};

export default function MapComponent({ items, center }: { items: Item[]; center: [number, number] }) {
  useEffect(() => {
    // Configure Leaflet icons only on client side
    const IconDefault = (L as any).Icon.Default;
    delete IconDefault.prototype._getIconUrl;
    IconDefault.mergeOptions({
      iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });
  }, []);

  const bounds = useMemo(() => {
    if (!items.length) return null;
    const latlngs = items.map((i) => [i.centerLat, i.centerLng]) as [number, number][];
    return L.latLngBounds(latlngs);
  }, [items]);

  return (
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
  );
}
