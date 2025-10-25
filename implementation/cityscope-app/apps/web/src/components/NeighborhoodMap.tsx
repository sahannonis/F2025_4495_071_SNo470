"use client";
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, Tooltip } from "react-leaflet";
import L from "leaflet";
import { useMemo, useEffect } from "react";

// Fix for default markers in react-leaflet
const DefaultIcon = new L.Icon({
  iconRetinaUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png",
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

type BaseItem = { id: number; name: string; centerLat: number; centerLng: number; score: number; onSelect?: (id: number) => void };
type Stop = { stop_id: string; stop_name: string; stop_lat: number; stop_lon: number };
type Mall = { name: string; lat: number; lon: number };

export default function NeighborhoodMap({
  items, center, stops = [], malls = []
}: {
  items: BaseItem[];
  center: [number, number];
  stops?: Stop[];
  malls?: Mall[];
}) {
  // Set the default icon for all markers
  useEffect(() => {
    // Set the default icon globally
    (L as any).Marker.prototype.options.icon = DefaultIcon;
  }, []);

  // Debug logging
  useEffect(() => {
    console.log('Map component received:', { 
      itemsCount: items.length, 
      stopsCount: stops.length, 
      mallsCount: malls.length,
      stops: stops.slice(0, 3), // Show first 3 stops
      malls: malls.slice(0, 3)  // Show first 3 malls
    });
  }, [items, stops, malls]);


  const bounds = useMemo(() => {
    if (!items.length) return null;
    const latlngs = items.map(i => [i.centerLat, i.centerLng]) as [number, number][];
    return L.latLngBounds(latlngs);
  }, [items]);

  return (
    <div className="rounded-xl overflow-hidden border h-96 relative">
      {/* Overlay indicators */}
      {(stops.length > 0 || malls.length > 0) && (
        <div className="absolute top-2 left-2 z-[1000] bg-white/90 backdrop-blur-sm rounded-lg p-2 text-xs font-medium shadow-lg">
          {stops.length > 0 && <div className="text-blue-600">🚌 {stops.length} stops</div>}
          {malls.length > 0 && <div className="text-red-600">🏬 {malls.length} malls</div>}
        </div>
      )}
      
      <MapContainer bounds={bounds || undefined} style={{ height: "100%", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {/* Neighborhood markers */}
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

        {/* Transit stops overlay */}
        {stops.map((s) => (
          <CircleMarker 
            center={[s.stop_lat, s.stop_lon]} 
            pathOptions={{ 
              radius: 8, 
              fillColor: '#3b82f6', 
              color: '#1e40af', 
              weight: 3, 
              opacity: 1, 
              fillOpacity: 0.8 
            }} 
            key={`stop-${s.stop_id}`}
          >
            <Tooltip>{s.stop_name || 'Stop'}</Tooltip>
          </CircleMarker>
        ))}

        {/* Malls overlay */}
        {malls.map((m, i) => (
          <CircleMarker 
            center={[m.lat, m.lon]} 
            pathOptions={{ 
              radius: 10, 
              fillColor: '#ef4444', 
              color: '#dc2626', 
              weight: 3, 
              opacity: 1, 
              fillOpacity: 0.8 
            }} 
            key={`mall-${i}`}
          >
            <Tooltip>{m.name || 'Mall'}</Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
