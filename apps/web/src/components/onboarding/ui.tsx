"use client";

import { cn } from "@/lib/utils";
import { HelpCircle } from "lucide-react";
import { useState } from "react";

export function FieldLabel({
  children,
  required,
  optional,
}: {
  children: React.ReactNode;
  required?: boolean;
  optional?: boolean;
}) {
  return (
    <div className="mb-1.5 flex items-center gap-2">
      <span className="text-sm font-medium text-ink">{children}</span>
      {required && <span className="text-xs text-coral">Required</span>}
      {optional && <span className="text-xs text-slate">Optional</span>}
    </div>
  );
}

export function HelpText({ children }: { children: React.ReactNode }) {
  return <p className="mt-1.5 text-xs leading-relaxed text-slate">{children}</p>;
}

export function ErrorText({ children }: { children?: React.ReactNode }) {
  if (!children) return null;
  return <p className="mt-1.5 text-xs font-medium text-coral">❌ {children}</p>;
}

export function Tooltip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  return (
    <span className="relative inline-flex">
      <button
        type="button"
        className="rounded-full p-0.5 text-slate hover:text-ink"
        aria-label="Help"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={() => setOpen((v) => !v)}
      >
        <HelpCircle className="h-3.5 w-3.5" />
      </button>
      {open && (
        <span className="absolute left-6 top-0 z-20 w-56 rounded-lg bg-ink px-3 py-2 text-xs leading-relaxed text-sand shadow-lg">
          {text}
        </span>
      )}
    </span>
  );
}

const inputClass =
  "w-full rounded-xl border border-ink/10 bg-white px-3.5 py-3 text-sm text-ink outline-none transition placeholder:text-slate/60 focus:border-pine focus:ring-2 focus:ring-pine/15";

export function TextInput(
  props: React.InputHTMLAttributes<HTMLInputElement> & { hasError?: boolean }
) {
  const { hasError, className, ...rest } = props;
  return (
    <input
      {...rest}
      className={cn(inputClass, hasError && "border-coral focus:border-coral focus:ring-coral/15", className)}
    />
  );
}

export function TextSelect(
  props: React.SelectHTMLAttributes<HTMLSelectElement> & { hasError?: boolean }
) {
  const { hasError, className, children, ...rest } = props;
  return (
    <select
      {...rest}
      className={cn(inputClass, hasError && "border-coral focus:border-coral focus:ring-coral/15", className)}
    >
      {children}
    </select>
  );
}

export function TextTextarea(
  props: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { hasError?: boolean }
) {
  const { hasError, className, ...rest } = props;
  return (
    <textarea
      {...rest}
      className={cn(inputClass, "min-h-[100px] resize-y", hasError && "border-coral", className)}
    />
  );
}

export function FeaturePill({
  label,
  selected,
  onToggle,
}: {
  label: string;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className={cn(
        "rounded-full border px-3.5 py-2 text-left text-sm transition",
        selected
          ? "border-pine bg-pine/10 text-pine shadow-sm"
          : "border-ink/10 bg-white text-ink hover:border-ink/25"
      )}
    >
      {selected ? "✓ " : ""}
      {label}
    </button>
  );
}

export function StepHeader({
  icon,
  title,
  description,
  step,
  total,
}: {
  icon: string;
  title: string;
  description: string;
  step: number;
  total: number;
}) {
  return (
    <div className="mb-8">
      <p className="text-xs font-medium uppercase tracking-[0.16em] text-pine">
        Step {step} of {total}
      </p>
      <h1 className="mt-2 font-display text-3xl tracking-tight text-ink md:text-4xl">
        <span className="mr-2" aria-hidden>
          {icon}
        </span>
        {title}
      </h1>
      <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate md:text-base">{description}</p>
    </div>
  );
}

export function SectionCard({
  title,
  children,
  className,
}: {
  title?: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-2xl border border-ink/8 bg-white/80 p-5 shadow-sm md:p-6", className)}>
      {title && <h3 className="mb-4 font-display text-lg text-ink">{title}</h3>}
      {children}
    </div>
  );
}
