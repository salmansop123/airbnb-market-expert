"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/lib/store";
import { cn } from "@/lib/utils";

const links = [
  { href: "/app", label: "Dashboard" },
  { href: "/app/properties", label: "Properties" },
  { href: "/app/predictions", label: "Predictions" },
  { href: "/app/market", label: "Market Analysis" },
  { href: "/app/reports", label: "Reports" },
  { href: "/app/chat", label: "AI Chat" },
  { href: "/app/billing", label: "Billing" },
  { href: "/app/settings", label: "Settings" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { accessToken, user, logout } = useAuth();

  useEffect(() => {
    if (!accessToken) router.replace("/login");
  }, [accessToken, router]);

  if (!accessToken) return null;

  return (
    <div className="flex min-h-screen bg-mist/30">
      <aside className="hidden w-64 shrink-0 border-r border-ink/10 bg-sand md:flex md:flex-col">
        <div className="px-6 py-6">
          <Link href="/app" className="font-display text-2xl">
            StayPrice
          </Link>
          <p className="mt-1 text-xs uppercase tracking-wider text-slate">{user?.plan || "free"} plan</p>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={cn(
                "block rounded-lg px-3 py-2 text-sm transition",
                pathname === l.href || (l.href !== "/app" && pathname.startsWith(l.href))
                  ? "bg-ink text-sand"
                  : "text-slate hover:bg-mist"
              )}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={() => {
            logout();
            router.push("/login");
          }}
          className="m-4 rounded-lg border border-ink/10 px-3 py-2 text-left text-sm"
        >
          Log out
        </button>
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="border-b border-ink/10 bg-sand/80 px-6 py-4 md:hidden">
          <span className="font-display text-xl">StayPrice</span>
        </div>
        <div className="p-6 md:p-10">{children}</div>
      </main>
    </div>
  );
}
