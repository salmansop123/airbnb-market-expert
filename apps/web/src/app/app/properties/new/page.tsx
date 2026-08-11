"use client";

import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ChevronLeft, ChevronRight, MapPin, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AMENITY_CATEGORY_META,
  BUILDING_TYPES,
  COUNTRIES,
  CURRENCIES,
  DEFAULT_FORM,
  FEATURE_OPTIONS,
  OnboardingForm,
  PROPERTY_TYPES,
  STEP_META,
  STORAGE_KEY,
  TOTAL_STEPS,
  US_STATES,
  isHouseLike,
} from "@/components/onboarding/constants";
import {
  ErrorText,
  FeaturePill,
  FieldLabel,
  HelpText,
  SectionCard,
  StepHeader,
  TextInput,
  TextSelect,
  TextTextarea,
  Tooltip,
} from "@/components/onboarding/ui";
import { ApiError, api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Amenity = { code: string; name: string; category: string };

const CONTENT_STEPS = 6; // excludes review for "Step X of 6" display on content; review shows separately

export default function NewPropertyPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<OnboardingForm>(DEFAULT_FORM);
  const [propertyId, setPropertyId] = useState<string | null>(null);
  const [amenities, setAmenities] = useState<Amenity[]>([]);
  const [files, setFiles] = useState<File[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState("");
  const [saving, setSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [detecting, setDetecting] = useState(false);
  const [showAdvancedGeo, setShowAdvancedGeo] = useState(false);
  const [openCats, setOpenCats] = useState<Record<string, boolean>>({ essentials: true, kitchen: true });
  const [hydrated, setHydrated] = useState(false);

  // Restore draft
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw) as {
          form?: OnboardingForm;
          step?: number;
          propertyId?: string | null;
        };
        if (parsed.form) setForm({ ...DEFAULT_FORM, ...parsed.form });
        if (parsed.step) setStep(Math.min(Math.max(parsed.step, 1), TOTAL_STEPS));
        if (parsed.propertyId) setPropertyId(parsed.propertyId);
      }
    } catch {
      /* ignore */
    }
    setHydrated(true);
  }, []);

  // Autosave draft locally
  useEffect(() => {
    if (!hydrated) return;
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ form, step, propertyId, savedAt: Date.now() })
    );
    setSavedAt(new Date().toLocaleTimeString());
  }, [form, step, propertyId, hydrated]);

  // Warn on unload
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (step < TOTAL_STEPS && form.title) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [step, form.title]);

  // Prefetch amenities when reaching that step (or restoring a draft there)
  useEffect(() => {
    if (step >= 5) {
      loadAmenities().catch(() => undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step]);

  const update = useCallback(<K extends keyof OnboardingForm>(key: K, value: OnboardingForm[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
    setErrors((e) => {
      if (!e[key as string]) return e;
      const next = { ...e };
      delete next[key as string];
      return next;
    });
  }, []);

  const percent = Math.round((step / TOTAL_STEPS) * 100);
  const meta = STEP_META[step - 1];

  const amenitiesByCategory = useMemo(() => {
    const map = new Map<string, Amenity[]>();
    for (const a of amenities) {
      const cat = a.category || "general";
      if (!map.has(cat)) map.set(cat, []);
      map.get(cat)!.push(a);
    }
    return Array.from(map.entries()).sort(([a], [b]) => {
      const order = Object.keys(AMENITY_CATEGORY_META);
      return (order.indexOf(a) === -1 ? 99 : order.indexOf(a)) - (order.indexOf(b) === -1 ? 99 : order.indexOf(b));
    });
  }, [amenities]);

  async function ensureProperty() {
    if (propertyId) return propertyId;
    const created = await api<{ id: string }>("/v1/properties", {
      method: "POST",
      body: JSON.stringify({
        title: form.title.trim() || "Untitled property",
        property_type: form.property_type,
      }),
    });
    setPropertyId(created.id);
    return created.id;
  }

  async function loadAmenities() {
    if (amenities.length) return;
    const list = await api<Amenity[]>("/v1/properties/amenities");
    setAmenities(list);
  }

  function validateStep(s: number): boolean {
    const next: Record<string, string> = {};
    if (s === 1) {
      if (!form.title.trim()) next.title = "Please enter your listing title.";
      if (!form.property_type) next.property_type = "Please select your property type.";
    }
    if (s === 2) {
      if (!form.country.trim()) next.country = "Please select a country.";
      if (!form.state.trim()) next.state = "Please enter or select a state / province.";
      if (!form.city.trim()) next.city = "Please enter your city.";
      if (!form.area.trim()) next.area = "Please enter the area or district.";
    }
    if (s === 3) {
      if (!form.bedrooms || Number(form.bedrooms) < 0) next.bedrooms = "Enter bedrooms.";
      if (!form.bathrooms || Number(form.bathrooms) < 0) next.bathrooms = "Enter bathrooms.";
      if (!form.guests || Number(form.guests) < 1) next.guests = "Maximum guests must be at least 1.";
    }
    if (s === 4) {
      if (!form.current_price || Number(form.current_price) <= 0) {
        next.current_price = "Current nightly price must be greater than zero.";
      }
      if (form.minimum_nights && Number(form.minimum_nights) < 1) {
        next.minimum_nights = "Minimum nights must be at least 1.";
      }
      if (
        form.maximum_nights &&
        form.minimum_nights &&
        Number(form.maximum_nights) < Number(form.minimum_nights)
      ) {
        next.maximum_nights = "Maximum nights must be greater than or equal to minimum nights.";
      }
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function persistStep(s: number) {
    const id = await ensureProperty();
    if (s === 1) {
      await api(`/v1/properties/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          title: form.title.trim(),
          property_type: form.property_type,
          building_type: form.building_type || null,
          floor_number: form.floor_number ? Number(form.floor_number) || null : null,
          onboarding_step: 2,
        }),
      });
    }
    if (s === 2) {
      await api(`/v1/properties/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          country: form.country,
          state: form.state,
          city: form.city,
          area: form.area || null,
          neighborhood: form.neighborhood || null,
          postal_code: form.postal_code || null,
          latitude: form.latitude ? Number(form.latitude) : null,
          longitude: form.longitude ? Number(form.longitude) : null,
          onboarding_step: 3,
        }),
      });
    }
    if (s === 3) {
      await api(`/v1/properties/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          bedrooms: Number(form.bedrooms),
          bathrooms: Number(form.bathrooms),
          beds: Number(form.beds),
          guests: Number(form.guests),
          square_feet: form.square_feet ? Number(form.square_feet) : null,
          features: form.features,
          onboarding_step: 4,
        }),
      });
    }
    if (s === 4) {
      await api(`/v1/properties/${id}`, {
        method: "PATCH",
        body: JSON.stringify({
          cleaning_fee: form.cleaning_fee ? Number(form.cleaning_fee) : null,
          extra_guest_fee: form.extra_guest_fee ? Number(form.extra_guest_fee) : null,
          minimum_nights: Number(form.minimum_nights) || 1,
          maximum_nights: Number(form.maximum_nights) || 30,
          current_price: form.current_price ? Number(form.current_price) : null,
          availability_notes: form.availability_notes
            ? `[${form.currency}] ${form.availability_notes}`
            : `Currency: ${form.currency}`,
          onboarding_step: 5,
        }),
      });
      await loadAmenities();
    }
    if (s === 5) {
      await api(`/v1/properties/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ amenity_codes: form.amenity_codes, onboarding_step: 6 }),
      });
    }
    if (s === 6 && files.length) {
      for (const file of files.slice(0, 30)) {
        const fd = new FormData();
        fd.append("file", file);
        await api(`/v1/properties/${id}/photos`, { method: "POST", body: fd });
      }
    }
    return id;
  }

  async function goNext() {
    setApiError("");
    if (step < TOTAL_STEPS && !validateStep(step)) return;
    setSaving(true);
    try {
      if (step < TOTAL_STEPS) {
        await persistStep(step);
        setStep((s) => s + 1);
        window.scrollTo({ top: 0, behavior: "smooth" });
      }
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 402) {
        setApiError(err.message + " Go to Billing to upgrade.");
      } else {
        setApiError(err instanceof Error ? err.message : "Something went wrong saving your progress.");
      }
    } finally {
      setSaving(false);
    }
  }

  async function submitFinal() {
    setApiError("");
    // Re-validate critical steps
    for (const s of [1, 2, 3, 4]) {
      if (!validateStep(s)) {
        setStep(s);
        setApiError("Please fix the highlighted fields before confirming.");
        return;
      }
    }
    setSaving(true);
    try {
      const id = await persistStep(5);
      if (files.length) await persistStep(6);
      await api(`/v1/properties/${id}/onboarding/complete`, { method: "POST" });
      localStorage.removeItem(STORAGE_KEY);
      router.push(`/app/properties/${id}`);
    } catch (err: unknown) {
      setApiError(err instanceof Error ? err.message : "Could not complete onboarding.");
    } finally {
      setSaving(false);
    }
  }

  function detectLocation() {
    if (!navigator.geolocation) {
      setApiError("Geolocation is not supported in this browser. Use Advanced to enter coordinates.");
      setShowAdvancedGeo(true);
      return;
    }
    setDetecting(true);
    setApiError("");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        update("latitude", pos.coords.latitude.toFixed(6));
        update("longitude", pos.coords.longitude.toFixed(6));
        setDetecting(false);
      },
      () => {
        setDetecting(false);
        setApiError("Could not detect location. You can enter coordinates under Advanced.");
        setShowAdvancedGeo(true);
      },
      { enableHighAccuracy: true, timeout: 12000 }
    );
  }

  function goBack() {
    setErrors({});
    setApiError("");
    setStep((s) => Math.max(1, s - 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  if (!hydrated) {
    return (
      <div className="mx-auto max-w-2xl animate-pulse space-y-4 py-10">
        <div className="h-4 w-32 rounded bg-mist" />
        <div className="h-10 w-2/3 rounded bg-mist" />
        <div className="h-40 rounded-2xl bg-mist" />
      </div>
    );
  }

  return (
    <div className="relative mx-auto min-h-[70vh] max-w-2xl pb-28">
      {/* Progress */}
      <div className="mb-6">
        <div className="flex items-center justify-between text-xs text-slate">
          <span>{percent}% complete</span>
          {savedAt && (
            <span className="flex items-center gap-1">
              <Sparkles className="h-3 w-3 text-pine" /> Draft saved {savedAt}
            </span>
          )}
        </div>
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-mist">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-pine to-coral"
            initial={false}
            animate={{ width: `${percent}%` }}
            transition={{ duration: 0.35 }}
          />
        </div>
        <div className="mt-3 flex gap-1.5">
          {STEP_META.map((s) => (
            <button
              key={s.id}
              type="button"
              title={s.title}
              disabled={s.id > step}
              onClick={() => s.id <= step && setStep(s.id)}
              className={cn(
                "h-1.5 flex-1 rounded-full transition",
                s.id < step && "bg-pine",
                s.id === step && "bg-coral",
                s.id > step && "bg-mist"
              )}
            />
          ))}
        </div>
      </div>

      {apiError && (
        <div className="mb-4 rounded-xl border border-coral/30 bg-coral/10 px-4 py-3 text-sm text-coral">
          {apiError}
        </div>
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={step}
          initial={{ opacity: 0, x: 16 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -16 }}
          transition={{ duration: 0.22 }}
        >
          <StepHeader
            icon={meta.icon}
            title={meta.title}
            description={meta.description}
            step={step === TOTAL_STEPS ? TOTAL_STEPS : Math.min(step, CONTENT_STEPS)}
            total={step === TOTAL_STEPS ? TOTAL_STEPS : CONTENT_STEPS}
          />

          {/* STEP 1 */}
          {step === 1 && (
            <div className="space-y-4">
              <SectionCard>
                <FieldLabel required>Property Type</FieldLabel>
                <TextSelect
                  hasError={!!errors.property_type}
                  value={form.property_type_label}
                  onChange={(e) => {
                    const label = e.target.value;
                    const match = PROPERTY_TYPES.find((p) => p.label === label);
                    update("property_type_label", label);
                    update("property_type", match?.value || "apartment");
                  }}
                >
                  {PROPERTY_TYPES.map((p) => (
                    <option key={p.label} value={p.label}>
                      {p.label}
                    </option>
                  ))}
                </TextSelect>
                <HelpText>Select the type that best describes your property.</HelpText>
                <ErrorText>{errors.property_type}</ErrorText>
              </SectionCard>

              <SectionCard>
                <FieldLabel required>Listing Title</FieldLabel>
                <TextInput
                  hasError={!!errors.title}
                  placeholder="Modern 2 Bedroom Apartment Near City Center"
                  value={form.title}
                  onChange={(e) => update("title", e.target.value)}
                  maxLength={120}
                />
                <HelpText>Give your property a short, attractive name.</HelpText>
                <ErrorText>{errors.title}</ErrorText>
              </SectionCard>

              <SectionCard>
                <div className="flex items-center gap-1.5">
                  <FieldLabel optional>Building Type</FieldLabel>
                  <Tooltip text="The type of building your property is located in." />
                </div>
                <TextSelect
                  value={form.building_type}
                  onChange={(e) => update("building_type", e.target.value)}
                >
                  <option value="">Select building type</option>
                  {BUILDING_TYPES.map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </TextSelect>
              </SectionCard>

              <SectionCard>
                <div className="flex items-center gap-1.5">
                  <FieldLabel optional>Floor Number</FieldLabel>
                  <Tooltip text="Leave empty if not applicable." />
                </div>
                <TextInput
                  placeholder={isHouseLike(form.property_type) ? "Ground Floor" : "2"}
                  value={form.floor_number}
                  onChange={(e) => update("floor_number", e.target.value)}
                />
                {isHouseLike(form.property_type) && (
                  <HelpText>Most houses are on the ground floor.</HelpText>
                )}
              </SectionCard>
            </div>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <div className="space-y-4">
              <SectionCard title="Address">
                <div className="space-y-4">
                  <div>
                    <FieldLabel required>Country</FieldLabel>
                    <TextSelect
                      hasError={!!errors.country}
                      value={form.country}
                      onChange={(e) => update("country", e.target.value)}
                    >
                      {COUNTRIES.map((c) => (
                        <option key={c} value={c}>
                          {c}
                        </option>
                      ))}
                    </TextSelect>
                    <ErrorText>{errors.country}</ErrorText>
                  </div>
                  <div>
                    <FieldLabel required>State / Province</FieldLabel>
                    {form.country === "United States" ? (
                      <TextSelect
                        hasError={!!errors.state}
                        value={form.state}
                        onChange={(e) => update("state", e.target.value)}
                      >
                        <option value="">Select state</option>
                        {US_STATES.map((s) => (
                          <option key={s} value={s}>
                            {s}
                          </option>
                        ))}
                      </TextSelect>
                    ) : (
                      <TextInput
                        hasError={!!errors.state}
                        placeholder="Punjab"
                        value={form.state}
                        onChange={(e) => update("state", e.target.value)}
                      />
                    )}
                    <ErrorText>{errors.state}</ErrorText>
                  </div>
                  <div>
                    <FieldLabel required>City</FieldLabel>
                    <TextInput
                      hasError={!!errors.city}
                      placeholder="Lahore"
                      value={form.city}
                      onChange={(e) => update("city", e.target.value)}
                    />
                    <ErrorText>{errors.city}</ErrorText>
                  </div>
                  <div>
                    <FieldLabel required>Area / District</FieldLabel>
                    <TextInput
                      hasError={!!errors.area}
                      placeholder="Downtown"
                      value={form.area}
                      onChange={(e) => update("area", e.target.value)}
                    />
                    <HelpText>Enter the district or local area.</HelpText>
                    <ErrorText>{errors.area}</ErrorText>
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <FieldLabel optional>Neighborhood</FieldLabel>
                      <Tooltip text="The smaller locality inside your area. Example: Area = DHA Phase 6, Neighborhood = Block C. If unknown, leave empty." />
                    </div>
                    <TextInput
                      placeholder="Green Park, Beverly Hills, Downtown West"
                      value={form.neighborhood}
                      onChange={(e) => update("neighborhood", e.target.value)}
                    />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <FieldLabel optional>Postal Code</FieldLabel>
                      <Tooltip text="Used for more accurate location matching." />
                    </div>
                    <TextInput
                      placeholder="54000"
                      value={form.postal_code}
                      onChange={(e) => update("postal_code", e.target.value)}
                    />
                  </div>
                </div>
              </SectionCard>

              <SectionCard title="Map coordinates">
                <p className="mb-4 text-sm text-slate">
                  You never need to type latitude or longitude. Detect your location instead.
                </p>
                <button
                  type="button"
                  onClick={detectLocation}
                  disabled={detecting}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-ink px-4 py-3 text-sm font-medium text-sand transition hover:bg-pine disabled:opacity-60 md:w-auto"
                >
                  <MapPin className="h-4 w-4" />
                  {detecting ? "Detecting…" : "Detect My Location"}
                </button>
                {(form.latitude || form.longitude) && (
                  <p className="mt-3 text-xs text-pine">
                    Located at {form.latitude}, {form.longitude}
                  </p>
                )}
                <button
                  type="button"
                  className="mt-4 flex items-center gap-1 text-xs text-slate underline"
                  onClick={() => setShowAdvancedGeo((v) => !v)}
                >
                  Advanced: edit coordinates manually
                  <ChevronDown className={cn("h-3.5 w-3.5 transition", showAdvancedGeo && "rotate-180")} />
                </button>
                {showAdvancedGeo && (
                  <div className="mt-3 grid gap-3 sm:grid-cols-2">
                    <div>
                      <FieldLabel optional>Latitude</FieldLabel>
                      <TextInput
                        placeholder="40.7128"
                        value={form.latitude}
                        onChange={(e) => update("latitude", e.target.value)}
                      />
                    </div>
                    <div>
                      <FieldLabel optional>Longitude</FieldLabel>
                      <TextInput
                        placeholder="-74.0060"
                        value={form.longitude}
                        onChange={(e) => update("longitude", e.target.value)}
                      />
                    </div>
                  </div>
                )}
              </SectionCard>
            </div>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <div className="space-y-4">
              <SectionCard title="Basic information">
                <div className="grid gap-4 sm:grid-cols-2">
                  {(
                    [
                      ["bedrooms", "Bedrooms", "2"],
                      ["bathrooms", "Bathrooms", "1"],
                      ["beds", "Beds", "2"],
                      ["guests", "Maximum Guests", "4"],
                      ["square_feet", "Square Feet", "850"],
                    ] as const
                  ).map(([key, label, ph]) => (
                    <div key={key} className={key === "square_feet" ? "sm:col-span-2" : ""}>
                      <FieldLabel required={key !== "square_feet"} optional={key === "square_feet"}>
                        {label}
                      </FieldLabel>
                      <TextInput
                        type="number"
                        min={0}
                        step={key === "bathrooms" ? 0.5 : 1}
                        placeholder={ph}
                        hasError={!!errors[key]}
                        value={form[key]}
                        onChange={(e) => update(key, e.target.value)}
                      />
                      <ErrorText>{errors[key]}</ErrorText>
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="Property features">
                <div className="flex flex-wrap gap-2">
                  {FEATURE_OPTIONS.map((f) => (
                    <FeaturePill
                      key={f.key}
                      label={f.label}
                      selected={!!form.features[f.key]}
                      onToggle={() =>
                        update("features", { ...form.features, [f.key]: !form.features[f.key] })
                      }
                    />
                  ))}
                </div>
              </SectionCard>
            </div>
          )}

          {/* STEP 4 */}
          {step === 4 && (
            <div className="space-y-4">
              <SectionCard>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <FieldLabel required>Current Nightly Price</FieldLabel>
                    <div className="flex gap-2">
                      <TextSelect
                        className="w-28 shrink-0"
                        value={form.currency}
                        onChange={(e) => update("currency", e.target.value)}
                      >
                        {CURRENCIES.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </TextSelect>
                      <TextInput
                        type="number"
                        min={1}
                        placeholder="120"
                        hasError={!!errors.current_price}
                        value={form.current_price}
                        onChange={(e) => update("current_price", e.target.value)}
                      />
                    </div>
                    <ErrorText>{errors.current_price}</ErrorText>
                  </div>
                  <div>
                    <FieldLabel optional>Cleaning Fee</FieldLabel>
                    <TextInput
                      type="number"
                      min={0}
                      placeholder="20"
                      value={form.cleaning_fee}
                      onChange={(e) => update("cleaning_fee", e.target.value)}
                    />
                  </div>
                  <div>
                    <FieldLabel optional>Extra Guest Fee</FieldLabel>
                    <TextInput
                      type="number"
                      min={0}
                      placeholder="15"
                      value={form.extra_guest_fee}
                      onChange={(e) => update("extra_guest_fee", e.target.value)}
                    />
                  </div>
                  <div>
                    <FieldLabel optional>Minimum Nights</FieldLabel>
                    <TextInput
                      type="number"
                      min={1}
                      placeholder="1"
                      hasError={!!errors.minimum_nights}
                      value={form.minimum_nights}
                      onChange={(e) => update("minimum_nights", e.target.value)}
                    />
                    <ErrorText>{errors.minimum_nights}</ErrorText>
                  </div>
                  <div>
                    <FieldLabel optional>Maximum Nights</FieldLabel>
                    <TextInput
                      type="number"
                      min={1}
                      placeholder="30"
                      hasError={!!errors.maximum_nights}
                      value={form.maximum_nights}
                      onChange={(e) => update("maximum_nights", e.target.value)}
                    />
                    <ErrorText>{errors.maximum_nights}</ErrorText>
                  </div>
                </div>
                <div className="mt-4">
                  <FieldLabel optional>Availability Notes</FieldLabel>
                  <TextTextarea
                    placeholder="Available every weekend except holidays…"
                    value={form.availability_notes}
                    onChange={(e) => update("availability_notes", e.target.value)}
                  />
                </div>
              </SectionCard>
            </div>
          )}

          {/* STEP 5 */}
          {step === 5 && (
            <div className="space-y-3">
              <p className="text-sm text-slate">
                {form.amenity_codes.length} selected · Tap a category to expand
              </p>
              {!amenities.length && (
                <SectionCard>
                  <p className="text-sm text-slate">Loading amenities…</p>
                </SectionCard>
              )}
              {amenitiesByCategory.map(([cat, items]) => {
                const metaCat = AMENITY_CATEGORY_META[cat] || AMENITY_CATEGORY_META.general;
                const open = openCats[cat] ?? false;
                const selectedCount = items.filter((i) => form.amenity_codes.includes(i.code)).length;
                return (
                  <div key={cat} className="overflow-hidden rounded-2xl border border-ink/8 bg-white shadow-sm">
                    <button
                      type="button"
                      className="flex w-full items-center justify-between px-5 py-4 text-left"
                      onClick={() => setOpenCats((o) => ({ ...o, [cat]: !open }))}
                    >
                      <span className="font-display text-lg">
                        <span className="mr-2">{metaCat.icon}</span>
                        {metaCat.label}
                        {selectedCount > 0 && (
                          <span className="ml-2 text-sm text-pine">({selectedCount})</span>
                        )}
                      </span>
                      <ChevronDown className={cn("h-4 w-4 text-slate transition", open && "rotate-180")} />
                    </button>
                    {open && (
                      <div className="flex flex-wrap gap-2 border-t border-ink/5 px-5 py-4">
                        {items.map((a) => (
                          <FeaturePill
                            key={a.code}
                            label={a.name}
                            selected={form.amenity_codes.includes(a.code)}
                            onToggle={() => {
                              const next = form.amenity_codes.includes(a.code)
                                ? form.amenity_codes.filter((c) => c !== a.code)
                                : [...form.amenity_codes, a.code];
                              update("amenity_codes", next);
                            }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* STEP 6 Photos */}
          {step === 6 && (
            <SectionCard>
              <FieldLabel optional>Upload photos</FieldLabel>
              <p className="mb-4 text-sm text-slate">
                10–30 photos recommended. You can skip and add later — Vision AI works better with photos.
              </p>
              <label className="flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-ink/15 bg-mist/40 px-6 py-10 text-center transition hover:border-pine/40">
                <span className="text-3xl">📷</span>
                <span className="mt-2 text-sm font-medium">Tap to choose photos</span>
                <span className="mt-1 text-xs text-slate">JPG, PNG · up to 30 files</span>
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={(e) => setFiles(Array.from(e.target.files || []).slice(0, 30))}
                />
              </label>
              {files.length > 0 && (
                <p className="mt-3 text-sm text-pine">{files.length} photo{files.length === 1 ? "" : "s"} selected</p>
              )}
            </SectionCard>
          )}

          {/* STEP 7 Review */}
          {step === 7 && (
            <div className="space-y-4">
              {[
                {
                  step: 1,
                  title: "Property",
                  rows: [
                    ["Type", form.property_type_label],
                    ["Title", form.title],
                    ["Building", form.building_type || "—"],
                    ["Floor", form.floor_number || "—"],
                  ],
                },
                {
                  step: 2,
                  title: "Location",
                  rows: [
                    ["Country", form.country],
                    ["State", form.state],
                    ["City", form.city],
                    ["Area", form.area],
                    ["Neighborhood", form.neighborhood || "—"],
                    ["Postal", form.postal_code || "—"],
                    ["Coords", form.latitude ? `${form.latitude}, ${form.longitude}` : "Not set"],
                  ],
                },
                {
                  step: 3,
                  title: "Details",
                  rows: [
                    ["Bedrooms", form.bedrooms],
                    ["Bathrooms", form.bathrooms],
                    ["Beds", form.beds],
                    ["Guests", form.guests],
                    ["Sq ft", form.square_feet || "—"],
                    [
                      "Features",
                      FEATURE_OPTIONS.filter((f) => form.features[f.key])
                        .map((f) => f.label)
                        .join(", ") || "—",
                    ],
                  ],
                },
                {
                  step: 4,
                  title: "Pricing",
                  rows: [
                    ["Nightly", `${form.currency} ${form.current_price}`],
                    ["Cleaning", form.cleaning_fee || "—"],
                    ["Extra guest", form.extra_guest_fee || "—"],
                    ["Nights", `${form.minimum_nights} – ${form.maximum_nights}`],
                  ],
                },
                {
                  step: 5,
                  title: "Amenities",
                  rows: [["Selected", `${form.amenity_codes.length} amenities`]],
                },
                {
                  step: 6,
                  title: "Photos",
                  rows: [["Files", files.length ? `${files.length} ready to upload` : "None (optional)"]],
                },
              ].map((block) => (
                <SectionCard key={block.title}>
                  <div className="mb-3 flex items-center justify-between">
                    <h3 className="font-display text-lg">{block.title}</h3>
                    <button
                      type="button"
                      className="text-xs font-medium text-pine underline"
                      onClick={() => setStep(block.step)}
                    >
                      Edit
                    </button>
                  </div>
                  <dl className="space-y-2 text-sm">
                    {block.rows.map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-4 border-b border-ink/5 pb-2 last:border-0">
                        <dt className="text-slate">{k}</dt>
                        <dd className="text-right font-medium text-ink">{v}</dd>
                      </div>
                    ))}
                  </dl>
                </SectionCard>
              ))}
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Sticky nav */}
      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-ink/10 bg-sand/95 px-4 py-3 backdrop-blur md:static md:mt-8 md:border-0 md:bg-transparent md:p-0 md:backdrop-blur-none">
        <div className="mx-auto flex max-w-2xl items-center justify-between gap-3">
          <button
            type="button"
            onClick={goBack}
            disabled={step === 1 || saving}
            className="inline-flex min-h-11 items-center gap-1 rounded-full border border-ink/15 px-5 py-2.5 text-sm font-medium disabled:opacity-40"
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>
          {step < TOTAL_STEPS ? (
            <button
              type="button"
              onClick={goNext}
              disabled={saving}
              className="inline-flex min-h-11 flex-1 items-center justify-center gap-1 rounded-full bg-pine px-5 py-2.5 text-sm font-medium text-sand shadow-lg shadow-pine/20 disabled:opacity-60 md:flex-none"
            >
              {saving ? "Saving…" : "Continue"}
              <ChevronRight className="h-4 w-4" />
            </button>
          ) : (
            <button
              type="button"
              onClick={submitFinal}
              disabled={saving}
              className="inline-flex min-h-11 flex-1 items-center justify-center gap-1 rounded-full bg-coral px-5 py-2.5 text-sm font-medium text-white shadow-lg shadow-coral/25 disabled:opacity-60 md:flex-none"
            >
              {saving ? "Creating…" : "Confirm & create property"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
