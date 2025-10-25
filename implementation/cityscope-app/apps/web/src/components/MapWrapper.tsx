"use client";
import dynamic from "next/dynamic";

// Create a dynamic wrapper for the map component that disables SSR
const DynamicMap = dynamic(() => import("./NeighborhoodMap"), {
  ssr: false,
  loading: () => (
    <div className="rounded-xl overflow-hidden border h-96 flex items-center justify-center bg-gray-100">
      <div className="text-gray-600">Loading map...</div>
    </div>
  ),
});

export default DynamicMap;
