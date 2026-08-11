"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api<{ message: string }>(
        "/v1/auth/register",
        {
          method: "POST",
          body: JSON.stringify({ email, password, full_name: fullName }),
        },
        false
      );
      setMessage(res.message + " Check API logs for the verification token in development.");
      setTimeout(() => router.push("/verify"), 1500);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-mist/40 px-4">
      <form onSubmit={onSubmit} className="w-full max-w-md rounded-2xl bg-sand p-8 shadow-sm">
        <Link href="/" className="font-display text-2xl">
          StayPrice
        </Link>
        <h1 className="mt-6 font-display text-3xl">Create your account</h1>
        {error && <p className="mt-4 text-sm text-coral">{error}</p>}
        {message && <p className="mt-4 text-sm text-pine">{message}</p>}
        <label className="mt-6 block text-sm">
          Full name
          <input
            className="mt-1 w-full rounded-lg border border-ink/10 bg-white px-3 py-2"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
        </label>
        <label className="mt-4 block text-sm">
          Email
          <input
            className="mt-1 w-full rounded-lg border border-ink/10 bg-white px-3 py-2"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label className="mt-4 block text-sm">
          Password
          <input
            className="mt-1 w-full rounded-lg border border-ink/10 bg-white px-3 py-2"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </label>
        <button disabled={loading} className="mt-6 w-full rounded-full bg-coral py-2.5 text-white">
          {loading ? "Creating…" : "Start free"}
        </button>
        <p className="mt-4 text-center text-sm text-slate">
          Have an account?{" "}
          <Link href="/login" className="text-pine underline">
            Log in
          </Link>
        </p>
      </form>
    </div>
  );
}
