"""OpenRouter AI provider abstraction."""
from __future__ import annotations

import json
import logging
from typing import Any, Protocol

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class AIProvider(Protocol):
    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str: ...


class OpenRouterProvider:
    def __init__(self) -> None:
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL.rstrip("/")
        self.default_model = settings.OPENROUTER_DEFAULT_MODEL

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        model: str | None = None,
        temperature: float = 0.3,
        response_format: dict | None = None,
    ) -> str:
        if not self.api_key:
            return self._mock_response(messages)
        payload: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": settings.FRONTEND_URL,
                    "X-Title": settings.APP_NAME,
                },
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    def _mock_response(self, messages: list[dict[str, Any]]) -> str:
        """Deterministic mock when OPENROUTER_API_KEY is unset."""
        last = messages[-1].get("content", "") if messages else ""
        text = last if isinstance(last, str) else json.dumps(last)
        if "vision" in text.lower() or "photo" in text.lower() or isinstance(last, list):
            return json.dumps(
                {
                    "quality_score": 78,
                    "luxury_score": 65,
                    "cleanliness_score": 82,
                    "lighting_score": 74,
                    "furniture_score": 70,
                    "overall_score": 74,
                    "details": {
                        "interior": "Modern and tidy",
                        "kitchen": "Functional",
                        "bedroom": "Comfortable",
                        "bathroom": "Clean",
                        "outdoor": "Limited",
                        "color_palette": "Neutral warm",
                    },
                    "missing_amenities": ["workspace", "coffee_maker"],
                    "suggestions": [
                        {"item": "Add desk workspace", "estimated_revenue_lift_pct": 4},
                        {"item": "Improve bedroom lighting", "estimated_revenue_lift_pct": 3},
                    ],
                    "estimated_revenue_impact": 8.0,
                }
            )
        if "recommend" in text.lower() or "improvement" in text.lower():
            return json.dumps(
                {
                    "strengths": ["Good location", "Competitive amenities"],
                    "weaknesses": ["Photos underlit", "Missing workspace"],
                    "recommendations": [
                        {
                            "title": "Upgrade listing photos",
                            "detail": "Hire a photographer for bright daytime shots",
                            "estimated_booking_lift_pct": 8,
                            "estimated_revenue_lift_pct": 10,
                        },
                        {
                            "title": "Add dedicated workspace",
                            "detail": "Desk + ergonomic chair appeals to remote workers",
                            "estimated_booking_lift_pct": 5,
                            "estimated_revenue_lift_pct": 6,
                        },
                    ],
                }
            )
        if "report" in text.lower():
            return "# StayPrice AI Report\n\n## Summary\nYour property is competitively positioned.\n\n## Price Recommendation\nSee dashboard for suggested nightly rate.\n"
        if "chat" in text.lower() or "question" in text.lower():
            return "Based on your comps and property profile, your suggested nightly rate balances occupancy and ADR. Focus on photo quality and a workspace amenity for the highest ROI."
        return json.dumps(
            {
                "suggested_adjustment_pct": 0,
                "rationale": "Base model price aligns with local comps.",
                "explanation": "Nearby similar listings cluster around the predicted band.",
            }
        )


_provider: OpenRouterProvider | None = None


def get_ai_provider() -> OpenRouterProvider:
    global _provider
    if _provider is None:
        _provider = OpenRouterProvider()
    return _provider


def parse_json_response(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        return {"raw": text}
