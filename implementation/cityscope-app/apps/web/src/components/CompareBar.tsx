"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

type Row = { name: string; avgRent: number; transitCount: number; mallCount: number; score: number };

export default function CompareBar({ data }: { data: Row[] }) {
  return (
    <div className="rounded-xl border p-4 h-80">
      <div className="text-sm text-gray-600 mb-2">Comparison</div>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="avgRent" fill="#8884d8" />
          <Bar dataKey="transitCount" fill="#82ca9d" />
          <Bar dataKey="mallCount" fill="#ffc658" />
          <Bar dataKey="score" fill="#ff6b6b" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
