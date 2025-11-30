"use client";

import { useEffect, useState } from "react";

export default function StatsCards({ 
  refreshFlag,
  onStatsLoaded, 
}: { refreshFlag: number;
  onStatsLoaded: (datasetsCount: number) => void;
 }) {
  const [stats, setStats] = useState<any>(null);

  const loadStats = () => {
    fetch("http://localhost:8000/api/stats")
      .then(res => res.json())
      .then(data => {
        setStats(data);
        onStatsLoaded(data.datasets);
      })
      .catch(err => console.log("Stats error:", err));
  };

  useEffect(() => {
    loadStats();
  }, [refreshFlag]);   // 👈 reload when refreshFlag changes

  if (!stats) {
    return (
      <div className="text-white text-center mb-10">
        Loading stats...
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-10 w-full">
      <Card label="Datasets" value={stats.datasets} />
      <Card label="Persons" value={stats.persons} />
      <Card label="Flights" value={stats.flights} />
      <Card label="Boxes" value={stats.boxes} />
      <Card label="Parabola" value={stats.parabola} />
    </div>
  );
}

function Card({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white border border-gray-200 p-4 rounded-xl text-center shadow-md">
      <p className="text-sm text-gray-600">{label}</p>
      <p className="text-3xl font-bold text-black">{value}</p>
    </div>
  );
}
