"use client";

import { useAuth } from "@/lib/store";

export default function SettingsPage() {
  const { user } = useAuth();
  return (
    <div>
      <h1 className="font-display text-4xl">Settings</h1>
      <div className="mt-8 max-w-lg space-y-4 rounded-2xl bg-sand p-6 text-sm">
        <div>
          <p className="text-slate">Email</p>
          <p className="font-medium">{user?.email}</p>
        </div>
        <div>
          <p className="text-slate">Name</p>
          <p className="font-medium">{user?.full_name || "—"}</p>
        </div>
        <div>
          <p className="text-slate">Plan</p>
          <p className="font-medium">{user?.plan}</p>
        </div>
        <div>
          <p className="text-slate">Verified</p>
          <p className="font-medium">{user?.is_verified ? "Yes" : "No"}</p>
        </div>
      </div>
    </div>
  );
}
