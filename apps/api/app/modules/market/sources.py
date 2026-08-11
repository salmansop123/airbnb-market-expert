"""Market data source abstraction + scraper helpers."""
from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

REGIONS = [
    {"slug": "New-York", "city": "New York", "lat": 40.7128, "lng": -74.0060},
    {"slug": "Los-Angeles", "city": "Los Angeles", "lat": 34.0522, "lng": -118.2437},
    {"slug": "Chicago", "city": "Chicago", "lat": 41.8781, "lng": -87.6298},
    {"slug": "Miami", "city": "Miami", "lat": 25.7617, "lng": -80.1918},
    {"slug": "San-Francisco", "city": "San Francisco", "lat": 37.7749, "lng": -122.4194},
]

TYPE_MAPPING = {
    "Rooms": "room",
    "Room": "room",
    "Place to stay": "apartment",
    "Home": "house",
    "Apartment": "apartment",
    "Condo": "apartment",
    "Villa": "villa",
    "Cabin": "cabin",
    "Hotel": "hotel",
    "Hostel": "hostel",
    "Tiny house": "tiny_house",
    "Boat": "boat",
    "Farm stay": "farm_stay",
}


@dataclass
class RawListing:
    external_id: str
    title: str | None
    price: float | None
    region: str
    city: str
    url: str | None = None
    property_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    bedrooms: int | None = None
    bathrooms: float | None = None
    rating: float | None = None
    review_count: int | None = None
    raw: dict | None = None


def parse_usd_price(text: str) -> float | None:
    match = re.search(r"\$[\d,]+(?:\.\d{2})?", text or "")
    if not match:
        return None
    return float(match.group().replace("$", "").replace(",", ""))


def nightly_from_total(total: float, nights: int | None = None) -> float:
    n = nights or 1
    return round(total / max(n, 1), 2)


def property_type_from_title(title: str | None) -> str | None:
    if not title or " in " not in title:
        return None
    raw = title.split(" in ")[0].strip()
    return TYPE_MAPPING.get(raw, raw.lower().replace(" ", "_"))


class MarketSource(ABC):
    @abstractmethod
    def fetch_region(self, region_slug: str) -> list[RawListing]:
        raise NotImplementedError


class SeedMarketSource(MarketSource):
    """Deterministic seed data for local/dev when live scrape is unavailable."""

    SEED = [
        ("apt-ny-1", "Apartment in Manhattan", 285, "New-York", "New York", "apartment", 2, 1.0, 4.8, 120),
        ("apt-ny-2", "Loft in Brooklyn", 220, "New-York", "New York", "apartment", 1, 1.0, 4.6, 80),
        ("house-ny-1", "House in Queens", 310, "New-York", "New York", "house", 3, 2.0, 4.7, 55),
        ("room-ny-1", "Room in Harlem", 95, "New-York", "New York", "room", 1, 1.0, 4.4, 200),
        ("apt-la-1", "Apartment in Santa Monica", 340, "Los-Angeles", "Los Angeles", "apartment", 2, 2.0, 4.9, 90),
        ("house-la-1", "House in Venice", 450, "Los-Angeles", "Los Angeles", "house", 3, 2.5, 4.8, 40),
        ("villa-la-1", "Villa in Hollywood Hills", 780, "Los-Angeles", "Los Angeles", "villa", 4, 3.0, 4.9, 22),
        ("apt-chi-1", "Apartment in River North", 195, "Chicago", "Chicago", "apartment", 1, 1.0, 4.5, 110),
        ("house-chi-1", "House in Lincoln Park", 275, "Chicago", "Chicago", "house", 3, 2.0, 4.7, 60),
        ("apt-mia-1", "Apartment in South Beach", 320, "Miami", "Miami", "apartment", 2, 2.0, 4.6, 150),
        ("villa-mia-1", "Villa in Coral Gables", 620, "Miami", "Miami", "villa", 4, 3.5, 4.9, 35),
        ("apt-sf-1", "Apartment in Mission", 290, "San-Francisco", "San Francisco", "apartment", 1, 1.0, 4.7, 95),
        ("house-sf-1", "House in Noe Valley", 410, "San-Francisco", "San Francisco", "house", 3, 2.0, 4.8, 48),
        ("cabin-1", "Cabin near Lake Tahoe", 260, "San-Francisco", "San Francisco", "cabin", 2, 1.0, 4.9, 70),
        ("boat-mia", "Boat in Miami Marina", 380, "Miami", "Miami", "boat", 1, 1.0, 4.5, 18),
    ]

    COORDS = {
        "New York": (40.7128, -74.0060),
        "Los Angeles": (34.0522, -118.2437),
        "Chicago": (41.8781, -87.6298),
        "Miami": (25.7617, -80.1918),
        "San Francisco": (37.7749, -122.4194),
    }

    def fetch_region(self, region_slug: str) -> list[RawListing]:
        out = []
        for row in self.SEED:
            ext_id, title, price, region, city, ptype, beds, baths, rating, reviews = row
            if region != region_slug:
                continue
            lat, lng = self.COORDS.get(city, (None, None))
            out.append(
                RawListing(
                    external_id=ext_id,
                    title=title,
                    price=float(price),
                    region=region,
                    city=city,
                    url=f"https://www.airbnb.com/rooms/{ext_id}",
                    property_type=ptype,
                    latitude=lat,
                    longitude=lng,
                    bedrooms=beds,
                    bathrooms=baths,
                    rating=rating,
                    review_count=reviews,
                    raw={"source": "seed"},
                )
            )
        return out


class PlaywrightMarketSource(MarketSource):
    """Best-effort Airbnb search scrape. Falls back to empty on failure."""

    def fetch_region(self, region_slug: str) -> list[RawListing]:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.warning("Playwright not available")
            return []

        listings: list[RawListing] = []
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                page.goto(f"https://www.airbnb.com/s/{region_slug}/homes", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(4000)
                titles = page.query_selector_all("[data-testid='listing-card-title']")
                prices = page.query_selector_all("[aria-label*='for']")
                city = region_slug.replace("-", " ")
                for i, (t, pr) in enumerate(zip(titles, prices)):
                    title = t.inner_text().strip() if t else None
                    raw_label = pr.get_attribute("aria-label") or ""
                    total = parse_usd_price(raw_label)
                    # Detect nights from label if present, else assume nightly already
                    nights_match = re.search(r"for\s+(\d+)\s+night", raw_label, re.I)
                    nights = int(nights_match.group(1)) if nights_match else 1
                    price = nightly_from_total(total, nights) if total else None
                    listings.append(
                        RawListing(
                            external_id=f"{region_slug}-{i}-{hash(title) % 10_000_000}",
                            title=title,
                            price=price,
                            region=region_slug,
                            city=city,
                            property_type=property_type_from_title(title),
                            raw={"aria_label": raw_label},
                        )
                    )
                browser.close()
        except Exception as exc:
            logger.exception("Playwright scrape failed for %s: %s", region_slug, exc)
            return []
        return listings


def get_market_source(prefer_live: bool = False) -> MarketSource:
    if prefer_live:
        return PlaywrightMarketSource()
    return SeedMarketSource()
