"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";

export default function VerifyPage() {
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      const res = await api<{ message: string }>(
        "/v1/auth/verify-email",
        { method: "POST", body: JSON.stringify({ token }) },
        false
      );
      setMessage(res.message);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Verification failed");
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-2xl bg-sand p-8">
        <h1 className="font-display text-3xl">Verify email</h1>
        <p className="mt-2 text-sm text-slate">Paste the token from your email (or API logs in dev).</p>
        {error && <p className="mt-3 text-coral text-sm">{error}</p>}
        {message && <p className="mt-3 text-pine text-sm">{message}</p>}
        <input
          className="mt-6 w-full rounded-lg border border-ink/10 px-3 py-2"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Verification token"
          required
        />
        <button className="mt-4 w-full rounded-full bg-ink py-2 text-sand">Verify</button>
        <Link href="/login" className="mt-4 block text-center text-sm text-pine underline">
          Continue to login
        </Link>
      </form>
    </div>
  );
}
