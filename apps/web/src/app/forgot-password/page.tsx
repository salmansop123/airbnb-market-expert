"use client";

import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [step, setStep] = useState<"request" | "reset">("request");
  const [message, setMessage] = useState("");

  async function requestReset(e: React.FormEvent) {
    e.preventDefault();
    const res = await api<{ message: string }>(
      "/v1/auth/forgot-password",
      { method: "POST", body: JSON.stringify({ email }) },
      false
    );
    setMessage(res.message);
    setStep("reset");
  }

  async function resetPassword(e: React.FormEvent) {
    e.preventDefault();
    const res = await api<{ message: string }>(
      "/v1/auth/reset-password",
      { method: "POST", body: JSON.stringify({ token, new_password: password }) },
      false
    );
    setMessage(res.message);
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-2xl bg-sand p-8">
        <h1 className="font-display text-3xl">Reset password</h1>
        {message && <p className="mt-3 text-sm text-pine">{message}</p>}
        {step === "request" ? (
          <form onSubmit={requestReset}>
            <input
              className="mt-6 w-full rounded-lg border px-3 py-2"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Email"
              required
            />
            <button className="mt-4 w-full rounded-full bg-ink py-2 text-sand">Send reset</button>
          </form>
        ) : (
          <form onSubmit={resetPassword}>
            <input
              className="mt-6 w-full rounded-lg border px-3 py-2"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Reset token"
              required
            />
            <input
              className="mt-3 w-full rounded-lg border px-3 py-2"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="New password"
              minLength={8}
              required
            />
            <button className="mt-4 w-full rounded-full bg-ink py-2 text-sand">Update password</button>
          </form>
        )}
        <Link href="/login" className="mt-4 block text-center text-sm underline">
          Back to login
        </Link>
      </div>
    </div>
  );
}
