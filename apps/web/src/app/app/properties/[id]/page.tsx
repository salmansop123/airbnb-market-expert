"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { STORAGE_KEY } from "@/components/onboarding/constants";

type Property = {
  id: string;
  title: string;
  city: string | null;
  property_type: string;
  bedrooms: number | null;
  bathrooms: number | null;
  current_price: number | null;
  onboarding_complete: boolean;
  photos: { id: string; url: string }[];
};

type Prediction = {
  id: string;
  status: string;
  suggested_price: number | null;
  min_price: number | null;
  max_price: number | null;
  monthly_revenue: number | null;
  annual_revenue: number | null;
  expected_occupancy: number | null;
  confidence_score: number | null;
  confidence_label?: string | null;
  pricing_method?: string | null;
  explanation: string | null;
  error_message?: string | null;
  progress?: { stage: string; percent: number; message: string; stages: string[] } | null;
  strengths: string[];
  weaknesses: string[];
  recommendations: { title?: string; detail?: string; estimated_revenue_lift_pct?: number }[];
  vision: Record<string, number | null> | null;
};

export default function PropertyDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();
  const qc = useQueryClient();
  const [activePred, setActivePred] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  const property = useQuery({
    queryKey: ["property", id],
    queryFn: () => api<Property>(`/v1/properties/${id}`),
  });

  const predictions = useQuery({
    queryKey: ["predictions", id],
    queryFn: () => api<Prediction[]>(`/v1/properties/${id}/predictions`),
  });

  const analyze = useMutation({
    mutationFn: () => api<Prediction>(`/v1/properties/${id}/analyze`, { method: "POST" }),
    onSuccess: (data) => {
      setActivePred(data.id);
      qc.invalidateQueries({ queryKey: ["predictions", id] });
    },
  });

  const remove = useMutation({
    mutationFn: () => api<void>(`/v1/properties/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          const draft = JSON.parse(raw) as { propertyId?: string };
          if (draft.propertyId === id) localStorage.removeItem(STORAGE_KEY);
        }
      } catch {
        /* ignore */
      }
      qc.invalidateQueries({ queryKey: ["properties"] });
      router.replace("/app/properties");
    },
    onError: (e: Error) => setDeleteError(e.message || "Could not delete property."),
  });

  const predDetail = useQuery({
    queryKey: ["prediction", activePred],
    queryFn: () => api<Prediction>(`/v1/predictions/${activePred}`),
    enabled: !!activePred,
    refetchInterval: (q) => {
      const s = q.state.data?.status;
      return s === "pending" || s === "running" ? 2000 : false;
    },
  });

  useEffect(() => {
    if (!activePred && predictions.data?.[0]) setActivePred(predictions.data[0].id);
  }, [predictions.data, activePred]);

  const p = property.data;
  const pred = predDetail.data || predictions.data?.[0];

  return (
    <div>
      <Link href="/app/properties" className="text-sm text-slate underline">
        ← Properties
      </Link>
      <div className="mt-4 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-4xl">{p?.title || "…"}</h1>
          <p className="mt-2 text-slate">
            {p?.city} · {p?.property_type} · {p?.bedrooms} bd / {p?.bathrooms} ba
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link href={`/app/chat?property=${id}`} className="rounded-full border px-4 py-2 text-sm">
            AI Chat
          </Link>
          <button
            onClick={() => analyze.mutate()}
            disabled={!p?.onboarding_complete || analyze.isPending}
            className="rounded-full bg-coral px-5 py-2 text-white disabled:opacity-50"
          >
            {analyze.isPending ? "Starting…" : "Run AI analysis"}
          </button>
          <button
            type="button"
            onClick={() => {
              setDeleteError("");
              setConfirmDelete(true);
            }}
            className="rounded-full border border-coral/40 px-4 py-2 text-sm text-coral transition hover:bg-coral/10"
          >
            Delete
          </button>
        </div>
      </div>

      {deleteError && (
        <p className="mt-4 rounded-xl bg-coral/10 px-4 py-3 text-sm text-coral">{deleteError}</p>
      )}

      {confirmDelete && (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-4 sm:items-center">
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="delete-property-detail-title"
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl"
          >
            <h2 id="delete-property-detail-title" className="font-display text-2xl">
              Delete this property?
            </h2>
            <p className="mt-2 text-sm text-slate">
              <span className="font-medium text-ink">{p?.title || "This property"}</span> will be
              removed from your account. This cannot be undone.
            </p>
            <div className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={() => setConfirmDelete(false)}
                disabled={remove.isPending}
                className="rounded-full border px-5 py-2.5 text-sm"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => remove.mutate()}
                disabled={remove.isPending}
                className="rounded-full bg-coral px-5 py-2.5 text-sm text-white disabled:opacity-50"
              >
                {remove.isPending ? "Deleting…" : "Delete property"}
              </button>
            </div>
          </div>
        </div>
      )}

      {p?.photos?.length ? (
        <div className="mt-8 flex gap-3 overflow-x-auto">
          {p.photos.map((ph) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img key={ph.id} src={ph.url} alt="" className="h-32 w-48 rounded-xl object-cover" />
          ))}
        </div>
      ) : null}

      {analyze.isError && (
        <p className="mt-4 rounded-xl bg-coral/10 px-4 py-3 text-sm text-coral">
          {(analyze.error as Error)?.message || "Could not start analysis. Check your plan limits."}
        </p>
      )}

      {!pred && !analyze.isPending && (
        <div className="mt-10 rounded-2xl border border-dashed border-ink/20 bg-sand p-10 text-center">
          <p className="font-display text-2xl">No analysis yet</p>
          <p className="mt-2 text-slate">Run AI analysis to get comps, vision scores, and a price band.</p>
          <button
            onClick={() => analyze.mutate()}
            disabled={!p?.onboarding_complete}
            className="mt-6 rounded-full bg-coral px-5 py-2 text-white disabled:opacity-50"
          >
            Run first analysis
          </button>
        </div>
      )}

      {pred && (
        <div className="mt-10 space-y-6">
          {(pred.status === "pending" || pred.status === "running") && (
            <div className="rounded-2xl bg-sand p-6">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium">{pred.progress?.message || "Analyzing…"}</span>
                <span className="text-slate">{pred.progress?.percent ?? 0}%</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-mist">
                <div
                  className="h-full bg-pine transition-all duration-500"
                  style={{ width: `${pred.progress?.percent ?? 5}%` }}
                />
              </div>
              <ol className="mt-4 grid gap-1 text-xs text-slate sm:grid-cols-4">
                {(pred.progress?.stages || []).map((s) => (
                  <li key={s} className={s === pred.progress?.stage ? "font-medium text-pine" : ""}>
                    {s.replace(/_/g, " ")}
                  </li>
                ))}
              </ol>
            </div>
          )}

          <div className="rounded-2xl bg-ink p-8 text-sand">
            <p className="text-sm uppercase tracking-wider text-mist/70">Status: {pred.status}</p>
            {pred.status === "completed" && (
              <>
                <p className="mt-4 font-display text-5xl">${pred.suggested_price}/night</p>
                <p className="mt-2 text-mist/80">
                  Band ${pred.min_price} – ${pred.max_price} · Confidence{" "}
                  {Math.round((pred.confidence_score || 0) * 100)}% ({pred.confidence_label || "n/a"})
                </p>
                <p className="mt-1 text-xs text-mist/60">
                  Method: {(pred.pricing_method || "model").replace(/_/g, " ")} — denser comps raise confidence.
                </p>
                <div className="mt-6 grid gap-4 sm:grid-cols-3">
                  <div>
                    <p className="text-xs text-mist/60">Occupancy</p>
                    <p className="font-display text-2xl">{Math.round((pred.expected_occupancy || 0) * 100)}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-mist/60">Monthly</p>
                    <p className="font-display text-2xl">${pred.monthly_revenue}</p>
                  </div>
                  <div>
                    <p className="text-xs text-mist/60">Annual</p>
                    <p className="font-display text-2xl">${pred.annual_revenue}</p>
                  </div>
                </div>
                {pred.explanation && <p className="mt-6 text-sm text-mist/90">{pred.explanation}</p>}
              </>
            )}
            {(pred.status === "pending" || pred.status === "running") && (
              <p className="mt-4">Agents are analyzing comps, vision, and pricing…</p>
            )}
            {pred.status === "failed" && (
              <p className="mt-4 text-coral">Analysis failed. {pred.error_message || "Try again."}</p>
            )}
          </div>

          {pred.status === "completed" && (
            <>
              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl bg-sand p-6">
                  <h2 className="font-display text-2xl">Strengths</h2>
                  <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
                    {(pred.strengths || []).map((s, i) => (
                      <li key={i}>{typeof s === "string" ? s : JSON.stringify(s)}</li>
                    ))}
                  </ul>
                </div>
                <div className="rounded-2xl bg-sand p-6">
                  <h2 className="font-display text-2xl">Weaknesses</h2>
                  <ul className="mt-3 list-disc space-y-1 pl-5 text-sm">
                    {(pred.weaknesses || []).map((s, i) => (
                      <li key={i}>{typeof s === "string" ? s : JSON.stringify(s)}</li>
                    ))}
                  </ul>
                </div>
              </div>
              <div className="rounded-2xl bg-sand p-6">
                <h2 className="font-display text-2xl">Recommendations</h2>
                <ul className="mt-4 space-y-4">
                  {(pred.recommendations || []).map((r, i) => (
                    <li key={i}>
                      <p className="font-medium">{r.title || "Improvement"}</p>
                      <p className="text-sm text-slate">{r.detail}</p>
                      {r.estimated_revenue_lift_pct != null && (
                        <p className="text-xs text-pine">+{r.estimated_revenue_lift_pct}% revenue lift est.</p>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
              {pred.vision && (
                <div className="rounded-2xl bg-sand p-6">
                  <h2 className="font-display text-2xl">Vision scores</h2>
                  <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
                    {Object.entries(pred.vision)
                      .filter(([, v]) => typeof v === "number")
                      .map(([k, v]) => (
                        <div key={k}>
                          <p className="text-xs text-slate">{k.replace(/_/g, " ")}</p>
                          <p className="font-display text-xl">{v}</p>
                        </div>
                      ))}
                  </div>
                </div>
              )}
              <GenerateReportButton predictionId={pred.id} />
            </>
          )}
        </div>
      )}
    </div>
  );
}

function GenerateReportButton({ predictionId }: { predictionId: string }) {
  const [msg, setMsg] = useState("");
  return (
    <button
      className="rounded-full border border-ink px-5 py-2 text-sm"
      onClick={async () => {
        try {
          const report = await api<{ url: string | null; status: string }>(
            `/v1/reports/predictions/${predictionId}/report`,
            { method: "POST" }
          );
          setMsg(report.url ? `Report ready: ${report.url}` : `Report ${report.status}`);
        } catch (e: unknown) {
          setMsg(e instanceof Error ? e.message : "Failed");
        }
      }}
    >
      {msg || "Generate PDF report (Pro)"}
    </button>
  );
}
