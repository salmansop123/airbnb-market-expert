"""Specialized AI agents for the revenue analysis pipeline."""
from __future__ import annotations

import json
from typing import Any

from app.core.config import get_settings
from app.modules.agents.provider import get_ai_provider, parse_json_response

settings = get_settings()


async def property_agent(property_data: dict[str, Any]) -> dict[str, Any]:
    provider = get_ai_provider()
    content = await provider.chat(
        [
            {
                "role": "system",
                "content": "You normalize short-term rental property profiles into a concise JSON brief.",
            },
            {
                "role": "user",
                "content": f"Normalize this property into JSON with keys: summary, guest_persona, positioning.\n{json.dumps(property_data)}",
            },
        ]
    )
    parsed = parse_json_response(content)
    if "raw" in parsed and len(parsed) == 1:
        return {"summary": content, "guest_persona": "leisure+business", "positioning": "mid-market"}
    return parsed


async def vision_agent(photo_urls: list[str]) -> dict[str, Any]:
    provider = get_ai_provider()
    if not photo_urls:
        return {
            "quality_score": 50,
            "luxury_score": 50,
            "cleanliness_score": 50,
            "lighting_score": 50,
            "furniture_score": 50,
            "overall_score": 50,
            "details": {},
            "missing_amenities": [],
            "suggestions": [],
            "estimated_revenue_impact": 0,
        }
    # Cap photos for cost
    urls = photo_urls[:12]
    user_content: list[dict[str, Any]] = [
        {
            "type": "text",
            "text": (
                "Analyze these Airbnb listing photos. Return JSON with quality_score, luxury_score, "
                "cleanliness_score, lighting_score, furniture_score, overall_score (0-100), details "
                "(interior, kitchen, bedroom, bathroom, outdoor, color_palette), missing_amenities, "
                "suggestions (list of {item, estimated_revenue_lift_pct}), estimated_revenue_impact."
            ),
        }
    ]
    for url in urls:
        user_content.append({"type": "image_url", "image_url": {"url": url}})
    content = await provider.chat(
        [{"role": "user", "content": user_content}],
        model=settings.OPENROUTER_VISION_MODEL,
    )
    return parse_json_response(content)


async def market_agent(property_data: dict[str, Any], comps: list[dict[str, Any]]) -> dict[str, Any]:
    provider = get_ai_provider()
    content = await provider.chat(
        [
            {
                "role": "system",
                "content": "You are a short-term rental market analyst. Return JSON.",
            },
            {
                "role": "user",
                "content": (
                    "Compare this property to comps. Return JSON with keys: "
                    "market_summary, competitive_position, price_gap_notes, demand_signals.\n"
                    f"Property: {json.dumps(property_data)}\nComps: {json.dumps(comps[:15])}"
                ),
            },
        ]
    )
    return parse_json_response(content)


async def pricing_agent(
    property_data: dict[str, Any],
    base_price: float,
    min_price: float,
    max_price: float,
    market_brief: dict[str, Any],
    vision: dict[str, Any],
) -> dict[str, Any]:
    provider = get_ai_provider()
    content = await provider.chat(
        [
            {
                "role": "system",
                "content": (
                    "You adjust STR nightly prices within ±12% of the model base. Return JSON with "
                    "suggested_price, min_price, max_price, suggested_adjustment_pct, rationale, explanation."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "property": property_data,
                        "base_price": base_price,
                        "min_price": min_price,
                        "max_price": max_price,
                        "market": market_brief,
                        "vision": {
                            "overall_score": vision.get("overall_score"),
                            "luxury_score": vision.get("luxury_score"),
                        },
                    }
                ),
            },
        ]
    )
    parsed = parse_json_response(content)
    adj = float(parsed.get("suggested_adjustment_pct") or 0)
    adj = max(-12, min(12, adj))
    suggested = round(base_price * (1 + adj / 100), 2)
    return {
        "suggested_price": float(parsed.get("suggested_price") or suggested),
        "min_price": float(parsed.get("min_price") or min_price),
        "max_price": float(parsed.get("max_price") or max_price),
        "suggested_adjustment_pct": adj,
        "rationale": parsed.get("rationale") or "Aligned with comps and vision quality.",
        "explanation": parsed.get("explanation") or parsed.get("rationale") or "",
    }


async def revenue_agent(suggested_price: float, occupancy: float, seasonality_mult: float = 1.0) -> dict[str, Any]:
    occ = max(0.2, min(0.95, occupancy * (0.95 + 0.05 * seasonality_mult)))
    monthly = round(suggested_price * 30 * occ, 2)
    annual = round(monthly * 12, 2)
    return {
        "expected_occupancy": round(occ, 3),
        "monthly_revenue": monthly,
        "annual_revenue": annual,
        "seasonality_multiplier": seasonality_mult,
    }


async def recommendation_agent(
    property_data: dict[str, Any],
    vision: dict[str, Any],
    market: dict[str, Any],
    pricing: dict[str, Any],
) -> dict[str, Any]:
    provider = get_ai_provider()
    content = await provider.chat(
        [
            {
                "role": "system",
                "content": "You recommend STR listing improvements. Return JSON with strengths, weaknesses, recommendations.",
            },
            {
                "role": "user",
                "content": (
                    "Produce improvement recommendations with estimated booking and revenue lift.\n"
                    f"Property: {json.dumps(property_data)}\nVision: {json.dumps(vision)}\n"
                    f"Market: {json.dumps(market)}\nPricing: {json.dumps(pricing)}"
                ),
            },
        ]
    )
    parsed = parse_json_response(content)
    return {
        "strengths": parsed.get("strengths") or [],
        "weaknesses": parsed.get("weaknesses") or [],
        "recommendations": parsed.get("recommendations") or [],
    }


async def report_agent(payload: dict[str, Any]) -> str:
    provider = get_ai_provider()
    return await provider.chat(
        [
            {
                "role": "system",
                "content": "Write a professional Markdown report for an Airbnb host about pricing and revenue.",
            },
            {
                "role": "user",
                "content": f"Create a report covering price recommendation, comps, revenue forecast, improvements.\n{json.dumps(payload)}",
            },
        ],
        model=settings.OPENROUTER_REPORT_MODEL,
    )


async def chat_agent(question: str, context: dict[str, Any]) -> str:
    provider = get_ai_provider()
    return await provider.chat(
        [
            {
                "role": "system",
                "content": (
                    "You are StayPrice AI Chat. Answer host questions using the provided property and "
                    "prediction context. Be concise and actionable."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{json.dumps(context)}\n\nQuestion: {question}",
            },
        ]
    )
