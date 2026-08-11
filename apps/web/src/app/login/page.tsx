"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/store";

export default function LoginPage() {
  const router = useRouter();
  const { setTokens, setUser } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const tokens = await api<{ access_token: string; refresh_token: string }>(
        "/v1/auth/login",
        { method: "POST", body: JSON.stringify({ email, password }) },
        false
      );
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await api<{
        id: string;
        email: string;
        full_name?: string;
        plan: string;
        is_verified: boolean;
      }>("/v1/auth/me");
      setUser(me);
      router.push("/app");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
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
        <h1 className="mt-6 font-display text-3xl">Welcome back</h1>
        <p className="mt-2 text-sm text-slate">Log in to your revenue workspace.</p>
        {error && <p className="mt-4 text-sm text-coral">{error}</p>}
        <label className="mt-6 block text-sm">
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
            required
          />
        </label>
        <button
          disabled={loading}
          className="mt-6 w-full rounded-full bg-ink py-2.5 text-sand disabled:opacity-60"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
        <p className="mt-4 text-center text-sm text-slate">
          No account?{" "}
          <Link href="/register" className="text-pine underline">
            Register
          </Link>
        </p>
        <p className="mt-2 text-center text-sm">
          <Link href="/forgot-password" className="text-slate underline">
            Forgot password
          </Link>
        </p>
      </form>
    </div>
  );
}
