"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/store";

type Plan = {
  code: string;
  name: string;
  description: string | null;
  property_limit: number | null;
  price_monthly_cents: number;
  features: Record<string, unknown>;
};

export default function BillingPage() {
  const { user, setUser } = useAuth();
  const [message, setMessage] = useState("");
  const plans = useQuery({
    queryKey: ["plans"],
    queryFn: () => api<Plan[]>("/v1/billing/plans"),
  });
  const usage = useQuery({
    queryKey: ["usage"],
    queryFn: () =>
      api<{
        plan: string;
        analyses_this_month: number;
        chat_today: number;
        entitlements: Record<string, unknown>;
      }>("/v1/billing/usage"),
  });

  async function checkout(plan: string) {
    const res = await api<{ checkout_url: string | null; message: string }>("/v1/billing/checkout?plan=" + plan, {
      method: "POST",
    });
    setMessage(res.message);
    if (res.checkout_url) {
      window.location.href = res.checkout_url;
    } else {
      // Dev upgrade — refresh me
      const me = await api<NonNullable<typeof user>>("/v1/auth/me");
      setUser(me);
    }
  }

  return (
    <div>
      <h1 className="font-display text-4xl">Billing</h1>
      <p className="mt-2 text-slate">
        Current plan: <strong>{user?.plan || usage.data?.plan || "free"}</strong>
      </p>
      {usage.data && (
        <div className="mt-4 rounded-xl bg-sand px-4 py-3 text-sm text-slate">
          Analyses this month: {usage.data.analyses_this_month}
          {typeof usage.data.entitlements.analyses_per_month === "number"
            ? ` / ${usage.data.entitlements.analyses_per_month}`
            : " (unlimited)"}
          {" · "}
          Chat today: {usage.data.chat_today}
          {typeof usage.data.entitlements.chat_per_day === "number"
            ? ` / ${usage.data.entitlements.chat_per_day}`
            : ""}
        </div>
      )}
      {message && <p className="mt-4 text-sm text-pine">{message}</p>}
      <div className="mt-10 grid gap-6 md:grid-cols-3">
        {(plans.data || []).map((p) => (
          <div key={p.code} className="rounded-2xl bg-sand p-6">
            <h2 className="font-display text-2xl">{p.name}</h2>
            <p className="mt-2 font-display text-3xl">
              ${(p.price_monthly_cents / 100).toFixed(0)}
              <span className="text-sm text-slate">/mo</span>
            </p>
            <p className="mt-2 text-sm text-slate">{p.description}</p>
            <p className="mt-2 text-xs text-slate">
              Properties: {p.property_limit ?? "Unlimited"}
            </p>
            {p.code !== "free" && (
              <button
                onClick={() => checkout(p.code)}
                className="mt-6 rounded-full bg-ink px-4 py-2 text-sm text-sand"
              >
                Upgrade to {p.name}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
