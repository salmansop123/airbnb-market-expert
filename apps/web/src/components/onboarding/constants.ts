/** Onboarding constants — UI labels map to existing API property_type enums. */

export const TOTAL_STEPS = 7; // 5 content + photos + review

export const STEP_META = [
  {
    id: 1,
    key: "property",
    icon: "🏠",
    title: "Property Information",
    description: "Tell us the basic details about your property so we can identify similar listings.",
  },
  {
    id: 2,
    key: "location",
    icon: "📍",
    title: "Property Location",
    description: "Your location helps AI compare your property with nearby listings.",
  },
  {
    id: 3,
    key: "details",
    icon: "🛏",
    title: "Property Details",
    description: "Tell us about your property's size and facilities.",
  },
  {
    id: 4,
    key: "pricing",
    icon: "💰",
    title: "Pricing Information",
    description: "This helps AI understand your current pricing strategy.",
  },
  {
    id: 5,
    key: "amenities",
    icon: "✨",
    title: "Amenities",
    description: "Select every amenity your guests can use.",
  },
  {
    id: 6,
    key: "photos",
    icon: "📷",
    title: "Photos",
    description: "Great photos improve Vision AI scores and price confidence. Optional for now.",
  },
  {
    id: 7,
    key: "review",
    icon: "✅",
    title: "Review & Confirm",
    description: "Check everything looks right before we create your listing profile.",
  },
] as const;

/** Display label → API PropertyType enum value */
export const PROPERTY_TYPES: { label: string; value: string }[] = [
  { label: "Apartment", value: "apartment" },
  { label: "House", value: "house" },
  { label: "Villa", value: "villa" },
  { label: "Cabin", value: "cabin" },
  { label: "Room", value: "room" },
  { label: "Shared Room", value: "room" },
  { label: "Entire Home", value: "house" },
  { label: "Townhouse", value: "house" },
  { label: "Condominium", value: "apartment" },
  { label: "Guest House", value: "house" },
  { label: "Hotel", value: "hotel" },
  { label: "Hostel", value: "hostel" },
  { label: "Tiny House", value: "tiny_house" },
  { label: "Farm Stay", value: "farm_stay" },
  { label: "Boat", value: "boat" },
  { label: "Other", value: "apartment" },
];

export const BUILDING_TYPES = [
  "Residential Building",
  "Apartment Complex",
  "Villa",
  "Detached House",
  "Semi-detached House",
  "Townhouse",
  "Commercial Building",
  "Hotel",
  "Resort",
  "Farmhouse",
  "Cabin",
  "Other",
];

export const COUNTRIES = [
  "United States",
  "Canada",
  "United Kingdom",
  "Australia",
  "Pakistan",
  "United Arab Emirates",
  "France",
  "Germany",
  "Spain",
  "Italy",
  "Mexico",
  "Other",
];

export const US_STATES = [
  "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
  "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
  "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
  "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
  "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
  "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
  "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
  "Wisconsin", "Wyoming", "District of Columbia",
];

export const FEATURE_OPTIONS: { key: string; label: string }[] = [
  { key: "balcony", label: "Balcony" },
  { key: "parking", label: "Parking" },
  { key: "garden", label: "Garden" },
  { key: "pool", label: "Pool" },
  { key: "kitchen", label: "Kitchen" },
  { key: "workspace", label: "Dedicated Workspace" },
  { key: "heating", label: "Heating" },
  { key: "air_conditioning", label: "Air Conditioning" },
  { key: "tv", label: "TV" },
  { key: "wifi", label: "WiFi" },
  { key: "elevator", label: "Elevator" },
  { key: "pet_friendly", label: "Pet Friendly" },
  { key: "smoking_allowed", label: "Smoking Allowed" },
  { key: "self_checkin", label: "Self Check-in" },
  { key: "wheelchair_accessible", label: "Wheelchair Accessible" },
];

export const CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD", "PKR", "AED"];

/** Preferred amenity category order + display labels */
export const AMENITY_CATEGORY_META: Record<string, { label: string; icon: string }> = {
  essentials: { label: "Essentials", icon: "🏠" },
  bathroom: { label: "Bathroom essentials", icon: "🛁" },
  climate: { label: "Climate", icon: "🌤" },
  entertainment: { label: "Entertainment", icon: "📺" },
  kitchen: { label: "Kitchen", icon: "☕" },
  family: { label: "Family", icon: "👶" },
  work: { label: "Lifestyle & Work", icon: "🏋" },
  facilities: { label: "Lifestyle & Work", icon: "🏋" },
  outdoor: { label: "Outdoor", icon: "🌊" },
  parking: { label: "Parking", icon: "🚗" },
  rules: { label: "Policies", icon: "🐶" },
  access: { label: "Access", icon: "🔑" },
  accessibility: { label: "Accessibility", icon: "♿" },
  safety: { label: "Safety", icon: "🔐" },
  location: { label: "Location perks", icon: "🗺" },
  views: { label: "Views", icon: "🌅" },
  general: { label: "Other", icon: "✨" },
};

export const STORAGE_KEY = "stayprice-onboarding-draft-v1";

export type OnboardingForm = {
  title: string;
  property_type: string;
  property_type_label: string;
  building_type: string;
  floor_number: string;
  country: string;
  state: string;
  city: string;
  area: string;
  neighborhood: string;
  postal_code: string;
  latitude: string;
  longitude: string;
  bedrooms: string;
  bathrooms: string;
  beds: string;
  guests: string;
  square_feet: string;
  cleaning_fee: string;
  extra_guest_fee: string;
  minimum_nights: string;
  maximum_nights: string;
  current_price: string;
  currency: string;
  availability_notes: string;
  features: Record<string, boolean>;
  amenity_codes: string[];
};

export const DEFAULT_FORM: OnboardingForm = {
  title: "",
  property_type: "apartment",
  property_type_label: "Apartment",
  building_type: "",
  floor_number: "",
  country: "United States",
  state: "",
  city: "",
  area: "",
  neighborhood: "",
  postal_code: "",
  latitude: "",
  longitude: "",
  bedrooms: "1",
  bathrooms: "1",
  beds: "1",
  guests: "2",
  square_feet: "",
  cleaning_fee: "",
  extra_guest_fee: "",
  minimum_nights: "1",
  maximum_nights: "30",
  current_price: "",
  currency: "USD",
  availability_notes: "",
  features: {},
  amenity_codes: [],
};

export function isHouseLike(type: string) {
  return ["house", "villa", "cabin", "farm_stay", "tiny_house"].includes(type);
}
