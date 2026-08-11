"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { api } from "@/lib/api";

type Property = { id: string; title: string };
type Prediction = {
  id: string;
  status: string;
  suggested_price: number | null;
  created_at?: string;
};

export default function PredictionsPage() {
  const properties = useQuery({
    queryKey: ["properties"],
    queryFn: () => api<Property[]>("/v1/properties"),
  });

  const all = useQuery({
    queryKey: ["all-predictions", properties.data?.map((p) => p.id).join(",")],
    enabled: !!properties.data?.length,
    queryFn: async () => {
      const rows: { property: Property; pred: Prediction }[] = [];
      for (const p of properties.data || []) {
        const preds = await api<Prediction[]>(`/v1/properties/${p.id}/predictions`);
        for (const pred of preds) rows.push({ property: p, pred });
      }
      return rows;
    },
  });

  return (
    <div>
      <h1 className="font-display text-4xl">Predictions</h1>
      <p className="mt-2 text-slate">History across your portfolio.</p>
      <div className="mt-8 space-y-3">
        {(all.data || []).map(({ property, pred }) => (
          <Link
            key={pred.id}
            href={`/app/properties/${property.id}`}
            className="flex justify-between rounded-xl bg-sand px-5 py-4"
          >
            <div>
              <p className="font-medium">{property.title}</p>
              <p className="text-sm text-slate">{pred.status}</p>
            </div>
            <span className="font-display text-xl">
              {pred.suggested_price != null ? `$${pred.suggested_price}` : "—"}
            </span>
          </Link>
        ))}
        {!all.data?.length && <p className="text-slate">No predictions yet.</p>}
      </div>
    </div>
  );
}
