"use client";

import { motion } from "framer-motion";
import Link from "next/link";

const features = [
  {
    title: "Vision-powered listing audits",
    body: "Upload photos and get luxury, lighting, and cleanliness scores with revenue impact estimates.",
  },
  {
    title: "Comparable market intel",
    body: "We research nearby listings and surface the comps that actually match your property.",
  },
  {
    title: "Explainable price bands",
    body: "Get suggested, min, and max nightly rates — plus the why behind every recommendation.",
  },
];

const steps = [
  "Create your property profile",
  "Upload photos & amenities",
  "AI researches comps & analyzes vision",
  "Receive price + revenue plan",
];

const faqs = [
  {
    q: "How is StayPrice different from PriceLabs?",
    a: "We focus on AI diagnosis — vision analysis, improvement ROI, and explainable pricing — not calendar push automation.",
  },
  {
    q: "Is there a free plan?",
    a: "Yes. Free includes up to 5 properties with basic AI analysis.",
  },
  {
    q: "Do I need an Airbnb connection?",
    a: "Not for MVP. Enter property details and photos; market comps are collected in the background.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="absolute inset-x-0 top-0 z-20 flex items-center justify-between px-6 py-5 md:px-12">
        <span className="font-display text-2xl tracking-tight text-ink">StayPrice</span>
        <nav className="flex items-center gap-6 text-sm text-slate">
          <a href="#features" className="hover:text-ink">
            Features
          </a>
          <a href="#pricing" className="hover:text-ink">
            Pricing
          </a>
          <Link href="/login" className="hover:text-ink">
            Log in
          </Link>
          <Link
            href="/register"
            className="rounded-full bg-ink px-4 py-2 text-sand transition hover:bg-pine"
          >
            Start free
          </Link>
        </nav>
      </header>

      <section className="relative min-h-[100svh] overflow-hidden bg-hero-glow">
        <div
          className="absolute inset-0 bg-cover bg-center opacity-40"
          style={{
            backgroundImage:
              "url(https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=2000&q=80)",
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-sand/40 via-sand/70 to-sand" />
        <div className="relative z-10 mx-auto flex min-h-[100svh] max-w-5xl flex-col justify-center px-6 pt-24 md:px-12">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 text-sm uppercase tracking-[0.2em] text-pine"
          >
            StayPrice AI
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.05 }}
            className="font-display text-5xl leading-[1.05] text-ink md:text-7xl"
          >
            Price your Airbnb with certainty.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.12 }}
            className="mt-6 max-w-xl text-lg text-slate"
          >
            AI researches comps, audits your photos, and recommends the nightly rate that grows revenue —
            with clear reasons and improvement ROI.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.18 }}
            className="mt-10 flex flex-wrap gap-4"
          >
            <Link href="/register" className="rounded-full bg-coral px-6 py-3 text-white shadow-lg shadow-coral/30">
              Analyze my property
            </Link>
            <a href="#how" className="rounded-full border border-ink/20 px-6 py-3 text-ink">
              See how it works
            </a>
          </motion.div>
        </div>
      </section>

      <section id="features" className="mx-auto max-w-6xl px-6 py-24 md:px-12">
        <h2 className="font-display text-4xl">Built for hosts who want clarity</h2>
        <p className="mt-3 max-w-2xl text-slate">One job per insight — not a dashboard dump.</p>
        <div className="mt-12 grid gap-10 md:grid-cols-3">
          {features.map((f, i) => (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.08 }}
            >
              <h3 className="font-display text-2xl">{f.title}</h3>
              <p className="mt-3 text-slate">{f.body}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="bg-ink py-20 text-sand">
        <div className="mx-auto grid max-w-6xl gap-8 px-6 md:grid-cols-3 md:px-12">
          {[
            ["+18%", "avg. ADR lift after photo fixes"],
            ["5 cities", "seed market coverage at launch"],
            ["<10 min", "to first price recommendation"],
          ].map(([stat, label]) => (
            <div key={label}>
              <div className="font-display text-5xl text-coral">{stat}</div>
              <p className="mt-2 text-mist/80">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="how" className="mx-auto max-w-6xl px-6 py-24 md:px-12">
        <h2 className="font-display text-4xl">How it works</h2>
        <ol className="mt-10 space-y-6">
          {steps.map((s, i) => (
            <li key={s} className="flex items-start gap-4">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-pine text-sm text-sand">
                {i + 1}
              </span>
              <span className="pt-1 text-lg">{s}</span>
            </li>
          ))}
        </ol>
      </section>

      <section id="pricing" className="bg-mist/60 py-24">
        <div className="mx-auto max-w-6xl px-6 md:px-12">
          <h2 className="font-display text-4xl">Simple pricing</h2>
          <div className="mt-12 grid gap-8 md:grid-cols-3">
            {[
              {
                name: "Free",
                price: "$0",
                items: ["5 properties", "Basic AI pricing", "Market comps"],
              },
              {
                name: "Pro",
                price: "$29",
                items: ["Unlimited properties", "Vision AI", "PDF reports", "Advanced agents"],
                highlight: true,
              },
              {
                name: "Business",
                price: "$99",
                items: ["Portfolio tools", "API access", "Multi-user (soon)"],
              },
            ].map((p) => (
              <div
                key={p.name}
                className={`rounded-2xl p-8 ${p.highlight ? "bg-ink text-sand" : "bg-sand"}`}
              >
                <h3 className="font-display text-2xl">{p.name}</h3>
                <p className="mt-2 font-display text-4xl">
                  {p.price}
                  <span className="text-base opacity-70">/mo</span>
                </p>
                <ul className="mt-6 space-y-2 text-sm opacity-90">
                  {p.items.map((i) => (
                    <li key={i}>• {i}</li>
                  ))}
                </ul>
                <Link
                  href="/register"
                  className={`mt-8 inline-block rounded-full px-5 py-2 text-sm ${
                    p.highlight ? "bg-coral text-white" : "bg-ink text-sand"
                  }`}
                >
                  Get started
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-6 py-24 md:px-12">
        <h2 className="font-display text-4xl">FAQ</h2>
        <div className="mt-10 space-y-8">
          {faqs.map((f) => (
            <div key={f.q}>
              <h3 className="text-lg font-medium">{f.q}</h3>
              <p className="mt-2 text-slate">{f.a}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-pine px-6 py-20 text-center text-sand md:px-12">
        <h2 className="font-display text-4xl md:text-5xl">Stop guessing your nightly rate.</h2>
        <Link href="/register" className="mt-8 inline-block rounded-full bg-sand px-6 py-3 text-ink">
          Start free — 5 properties
        </Link>
      </section>

      <footer className="border-t border-ink/10 px-6 py-10 text-sm text-slate md:px-12">
        <div className="mx-auto flex max-w-6xl flex-wrap justify-between gap-4">
          <span className="font-display text-ink">StayPrice AI</span>
          <span>© {new Date().getFullYear()} StayPrice. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
}
