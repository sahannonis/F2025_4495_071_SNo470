"use client";
import { scoreColor } from "@/lib/colors";

export default function ScoreCards({
  summary,
}: {
  summary: { avgRent: number; transitCount: number; mallCount: number; score: number };
}) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 my-4">
      <div className="rounded-xl border p-4">
        <div className="text-sm text-gray-500">Avg Rent</div>
        <div className="text-2xl font-semibold">${summary.avgRent}</div>
      </div>
      <div className="rounded-xl border p-4">
        <div className="text-sm text-gray-500">Transit Stops</div>
        <div className="text-2xl font-semibold">{summary.transitCount}</div>
      </div>
      <div className="rounded-xl border p-4">
        <div className="text-sm text-gray-500">Malls</div>
        <div className="text-2xl font-semibold">{summary.mallCount}</div>
      </div>
      <div className={`rounded-xl p-4 text-white ${scoreColor(summary.score)}`}>
        <div className="text-sm opacity-90">Neighborhood Score</div>
        <div className="text-2xl font-semibold">{summary.score}/100</div>
      </div>
    </div>
  );
}
