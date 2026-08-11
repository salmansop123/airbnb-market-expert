"use client";

import { useQuery } from "@tanstack/react-query";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api } from "@/lib/api";

type Trend = {
  city: string;
  listing_count: number;
  avg_price: number | null;
  median_price: number | null;
  min_price: number | null;
  max_price: number | null;
};

export default function MarketPage() {
  const trends = useQuery({
    queryKey: ["trends"],
    queryFn: () => api<Trend[]>("/v1/market/trends"),
  });

  return (
    <div>
      <h1 className="font-display text-4xl">Market analysis</h1>
      <p className="mt-2 text-slate">City-level demand and rate trends from scraped comps.</p>
      <div className="mt-10 h-80 rounded-2xl bg-sand p-6">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={trends.data || []}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="city" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="avg_price" fill="#E85D4C" name="Avg price" radius={[6, 6, 0, 0]} />
            <Bar dataKey="median_price" fill="#1F6B5A" name="Median" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-8 overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b text-slate">
              <th className="py-2">City</th>
              <th>Listings</th>
              <th>Avg</th>
              <th>Median</th>
              <th>Min</th>
              <th>Max</th>
            </tr>
          </thead>
          <tbody>
            {(trends.data || []).map((t) => (
              <tr key={t.city} className="border-b border-ink/5">
                <td className="py-3 font-medium">{t.city}</td>
                <td>{t.listing_count}</td>
                <td>${t.avg_price}</td>
                <td>${t.median_price}</td>
                <td>${t.min_price}</td>
                <td>${t.max_price}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
