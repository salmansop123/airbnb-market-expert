"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import { STORAGE_KEY } from "@/components/onboarding/constants";

type Property = {
  id: string;
  title: string;
  city: string | null;
  property_type: string;
  onboarding_complete: boolean;
  current_price: number | null;
};

export default function PropertiesPage() {
  const qc = useQueryClient();
  const [confirmId, setConfirmId] = useState<string | null>(null);
  const [error, setError] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["properties"],
    queryFn: () => api<Property[]>("/v1/properties"),
  });

  const remove = useMutation({
    mutationFn: (id: string) => api<void>(`/v1/properties/${id}`, { method: "DELETE" }),
    onSuccess: (_data, id) => {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          const draft = JSON.parse(raw) as { propertyId?: string };
          if (draft.propertyId === id) localStorage.removeItem(STORAGE_KEY);
        }
      } catch {
        /* ignore */
      }
      setConfirmId(null);
      setError("");
      qc.invalidateQueries({ queryKey: ["properties"] });
    },
    onError: (e: Error) => setError(e.message || "Could not delete property."),
  });

  const pending = data?.find((p) => p.id === confirmId);

  return (
    <div>
      <div className="flex items-end justify-between">
        <div>
          <h1 className="font-display text-4xl">Properties</h1>
          <p className="mt-2 text-slate">Free plan: up to 5 properties.</p>
        </div>
        <Link href="/app/properties/new" className="rounded-full bg-ink px-5 py-2.5 text-sand">
          New property
        </Link>
      </div>
      {error && (
        <p className="mt-4 rounded-xl bg-coral/10 px-4 py-3 text-sm text-coral">{error}</p>
      )}
      {isLoading && <p className="mt-8 text-slate">Loading…</p>}
      <div className="mt-8 space-y-3">
        {(data || []).map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between gap-3 rounded-xl bg-sand px-5 py-4 transition hover:bg-mist"
          >
            <Link href={`/app/properties/${p.id}`} className="min-w-0 flex-1">
              <p className="font-medium">{p.title}</p>
              <p className="text-sm text-slate">
                {p.city || "No city"} · {p.property_type.replace("_", " ")}
                {!p.onboarding_complete && " · onboarding incomplete"}
              </p>
            </Link>
            <div className="flex shrink-0 items-center gap-3">
              <span className="text-sm text-pine">{p.current_price ? `$${p.current_price}` : "Set price"}</span>
              <button
                type="button"
                onClick={() => {
                  setError("");
                  setConfirmId(p.id);
                }}
                className="rounded-full border border-coral/40 px-3 py-1.5 text-xs font-medium text-coral transition hover:bg-coral/10"
                aria-label={`Delete ${p.title}`}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
        {!isLoading && !data?.length && (
          <p className="text-slate">No properties yet. Create your first listing profile.</p>
        )}
      </div>

      {confirmId && pending && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-4 sm:items-center">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-property-title"
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
          >
            <h2 id="delete-property-title" className="font-display text-2xl">
              Delete this property?
            </h2>
            <p className="mt-2 text-sm text-slate">
              <span className="font-medium text-ink">{pending.title}</span> will be removed from your
              account. This cannot be undone.
            </p>
            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => setConfirmId(null)}
                disabled={remove.isPending}
                className="rounded-full border px-5 py-2.5 text-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => remove.mutate(confirmId)}
                disabled={remove.isPending}
                className="rounded-full bg-coral px-5 py-2.5 text-sm text-white disabled:opacity-50"
              >
                {remove.isPending ? "Deleting…" : "Delete property"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
