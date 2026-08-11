"""CatBoost pricing model train/infer."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FEATURE_COLS = [
    "city",
    "property_type",
    "bedrooms",
    "bathrooms",
    "beds",
    "guests",
    "latitude",
    "longitude",
    "current_price",
    "comp_median",
    "comp_p75",
    "vision_overall",
    "amenity_count",
]
CAT_FEATURES = ["city", "property_type"]


def artifacts_dir() -> Path:
    p = Path(settings.MODEL_ARTIFACTS_DIR)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _default_row(features: dict[str, Any]) -> dict[str, Any]:
    return {
        "city": features.get("city") or "Unknown",
        "property_type": features.get("property_type") or "apartment",
        "bedrooms": float(features.get("bedrooms") or 1),
        "bathrooms": float(features.get("bathrooms") or 1),
        "beds": float(features.get("beds") or 1),
        "guests": float(features.get("guests") or 2),
        "latitude": float(features.get("latitude") or 0),
        "longitude": float(features.get("longitude") or 0),
        "current_price": float(features.get("current_price") or 0),
        "comp_median": float(features.get("comp_median") or 200),
        "comp_p75": float(features.get("comp_p75") or 250),
        "vision_overall": float(features.get("vision_overall") or 70),
        "amenity_count": float(features.get("amenity_count") or 5),
    }


def train_from_dataframe(df: pd.DataFrame, version: str = "v1") -> dict[str, Any]:
    if "price" not in df.columns:
        raise ValueError("Training data requires 'price' column")
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0 if col not in CAT_FEATURES else "Unknown"
    df = df.dropna(subset=["price"])
    df = df[(df["price"] >= 10) & (df["price"] <= 10000)]
    if len(df) < 5:
        raise ValueError("Need at least 5 rows to train")

    X = df[FEATURE_COLS].copy()
    y = df["price"].astype(float)
    for c in CAT_FEATURES:
        X[c] = X[c].astype(str)

    model = CatBoostRegressor(
        iterations=200,
        depth=6,
        learning_rate=0.08,
        loss_function="RMSE",
        verbose=False,
        random_seed=42,
    )
    model.fit(Pool(X, y, cat_features=CAT_FEATURES))
    preds = model.predict(X)
    mae = float(np.mean(np.abs(preds - y)))
    path = artifacts_dir() / f"catboost_{version}.cbm"
    model.save_model(str(path))
    meta = {"version": version, "mae": mae, "n_rows": len(df), "path": str(path)}
    joblib.dump(meta, artifacts_dir() / f"catboost_{version}_meta.pkl")
    # Mark active
    joblib.dump(meta, artifacts_dir() / "active_model.pkl")
    return meta


def _heuristic_predict(features: dict[str, Any]) -> tuple[float, float, float]:
    base = float(features.get("comp_median") or features.get("current_price") or 200)
    vision = float(features.get("vision_overall") or 70)
    amenity = float(features.get("amenity_count") or 5)
    adj = 1.0 + (vision - 70) / 500 + (amenity - 5) / 100
    suggested = round(base * adj, 2)
    return round(suggested * 0.85, 2), suggested, round(suggested * 1.2, 2)


def predict_price_band(features: dict[str, Any]) -> dict[str, Any]:
    row = _default_row(features)
    active = artifacts_dir() / "active_model.pkl"
    if not active.exists():
        lo, mid, hi = _heuristic_predict(row)
        return {
            "min_price": lo,
            "suggested_price": mid,
            "max_price": hi,
            "model_version": "heuristic-v0",
            "confidence": 0.45,
        }
    meta = joblib.load(active)
    model = CatBoostRegressor()
    model.load_model(meta["path"])
    X = pd.DataFrame([row])[FEATURE_COLS]
    for c in CAT_FEATURES:
        X[c] = X[c].astype(str)
    mid = float(model.predict(X)[0])
    # Quantile-ish band via residual MAE
    mae = float(meta.get("mae") or mid * 0.12)
    lo = max(10, round(mid - 1.5 * mae, 2))
    hi = round(mid + 1.5 * mae, 2)
    conf = min(0.92, 0.55 + min(len(str(meta.get("n_rows", 0))), 100) / 200)
    return {
        "min_price": lo,
        "suggested_price": round(mid, 2),
        "max_price": hi,
        "model_version": meta.get("version", "v1"),
        "confidence": round(conf, 3),
    }


def seed_and_train() -> dict[str, Any]:
    """Train on synthetic + seed market-like rows so inference works out of the box."""
    rows = []
    cities = ["New York", "Los Angeles", "Chicago", "Miami", "San Francisco"]
    types = ["apartment", "house", "villa", "room", "cabin"]
    rng = np.random.default_rng(42)
    for _ in range(120):
        city = cities[int(rng.integers(0, len(cities)))]
        ptype = types[int(rng.integers(0, len(types)))]
        beds = int(rng.integers(1, 5))
        base = {"New York": 280, "Los Angeles": 300, "Chicago": 200, "Miami": 270, "San Francisco": 290}[city]
        type_mult = {"apartment": 1.0, "house": 1.25, "villa": 1.8, "room": 0.45, "cabin": 1.1}[ptype]
        price = base * type_mult * (0.85 + 0.3 * rng.random()) * (0.9 + 0.1 * beds)
        rows.append(
            {
                "city": city,
                "property_type": ptype,
                "bedrooms": beds,
                "bathrooms": max(1, beds - 0.5),
                "beds": beds,
                "guests": beds * 2,
                "latitude": 0,
                "longitude": 0,
                "current_price": price * 0.95,
                "comp_median": price * 0.98,
                "comp_p75": price * 1.1,
                "vision_overall": float(rng.integers(55, 95)),
                "amenity_count": int(rng.integers(3, 20)),
                "price": round(price, 2),
            }
        )
    df = pd.DataFrame(rows)
    return train_from_dataframe(df, version="seed-v1")
