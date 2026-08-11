"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
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

type Property = { id: string; title: string; city: string | null; current_price: number | null };
type Trend = { city: string; avg_price: number | null; listing_count: number };
type Notification = { id: string; title: string; body: string; is_read: boolean };

export default function DashboardPage() {
  const properties = useQuery({
    queryKey: ["properties"],
    queryFn: () => api<Property[]>("/v1/properties"),
  });
  const trends = useQuery({
    queryKey: ["trends"],
    queryFn: () => api<Trend[]>("/v1/market/trends"),
  });
  const notifications = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api<Notification[]>("/v1/notifications"),
  });
  const usage = useQuery({
    queryKey: ["usage"],
    queryFn: () =>
      api<{ plan: string; analyses_this_month: number; entitlements: { analyses_per_month: number | null } }>(
        "/v1/billing/usage"
      ),
  });

  const props = properties.data || [];
  const avg =
    props.length && props.some((p) => p.current_price)
      ? Math.round(
          props.filter((p) => p.current_price).reduce((s, p) => s + (p.current_price || 0), 0) /
            props.filter((p) => p.current_price).length
        )
      : 0;

  if (properties.isLoading) {
    return (
      <div className="animate-pulse space-y-6">
        <div className="h-10 w-48 rounded bg-mist" />
        <div className="grid gap-6 sm:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-mist" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl">Dashboard</h1>
          <p className="mt-2 text-slate">Your revenue command center.</p>
        </div>
        <Link href="/app/properties/new" className="rounded-full bg-coral px-5 py-2.5 text-white">
          Add property
        </Link>
      </div>

      {!props.length && (
        <div className="mt-10 rounded-2xl border border-dashed border-ink/20 bg-sand p-10 text-center">
          <p className="font-display text-3xl">Welcome to StayPrice</p>
          <p className="mt-2 text-slate">Add your first property to get an AI price recommendation.</p>
          <Link href="/app/properties/new" className="mt-6 inline-block rounded-full bg-ink px-5 py-2.5 text-sand">
            Create property
          </Link>
        </div>
      )}

      <div className="mt-10 grid gap-6 sm:grid-cols-4">
        {[
          ["Properties", String(props.length)],
          ["Avg listed price", avg ? `$${avg}` : "—"],
          ["Markets tracked", String(trends.data?.length || 0)],
          [
            "Analyses this month",
            usage.data
              ? `${usage.data.analyses_this_month}${
                  usage.data.entitlements.analyses_per_month != null
                    ? ` / ${usage.data.entitlements.analyses_per_month}`
                    : ""
                }`
              : "—",
          ],
        ].map(([label, value]) => (
          <div key={label} className="rounded-2xl bg-sand p-6">
            <p className="text-sm text-slate">{label}</p>
            <p className="mt-2 font-display text-3xl">{value}</p>
          </div>
        ))}
      </div>

      <div className="mt-10 grid gap-8 lg:grid-cols-2">
        <div className="rounded-2xl bg-sand p-6">
          <h2 className="font-display text-2xl">Avg price by market</h2>
          <div className="mt-6 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trends.data || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="city" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="avg_price" fill="#1F6B5A" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
        <div className="rounded-2xl bg-sand p-6">
          <h2 className="font-display text-2xl">Recent notifications</h2>
          <ul className="mt-4 space-y-3">
            {(notifications.data || []).slice(0, 5).map((n) => (
              <li key={n.id} className="border-b border-ink/5 pb-3 text-sm">
                <p className="font-medium">{n.title}</p>
                <p className="text-slate">{n.body}</p>
              </li>
            ))}
            {!notifications.data?.length && <p className="text-sm text-slate">No notifications yet.</p>}
          </ul>
        </div>
      </div>
    </div>
  );
}
