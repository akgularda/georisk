from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"
CACHE_DIR = REPO_ROOT / "artifacts" / "ai" / "openrouter"


@dataclass(frozen=True)
class CountryNarrative:
    report_summary: str
    social_summary_line: str
    social_headline: str
    social_body: str


def openrouter_is_configured() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def resolve_openrouter_model() -> str:
    return os.getenv("OPENROUTER_MODEL") or DEFAULT_MODEL


def resolve_openrouter_base_url() -> str:
    return os.getenv("OPENROUTER_BASE_URL") or DEFAULT_BASE_URL


def _cache_path(payload: dict[str, Any]) -> Path:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{digest}.json"


def _strip_code_fences(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped
        if stripped.endswith("```"):
            stripped = stripped[:-3]
    return stripped.strip()


def _safe_text(value: Any, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback
    cleaned = " ".join(value.split())
    return cleaned or fallback


def maybe_generate_country_narrative(
    *,
    country_name: str,
    region_name: str | None,
    predicted_conflict_label: str | None = None,
    forecast_target: str,
    horizon_days: int,
    risk_level: str | None,
    forecast_probability: float | None,
    summary_fallback: str,
    social_summary_fallback: str,
    social_headline_fallback: str,
    social_body_fallback: str,
    top_drivers: list[str],
    chronology: list[str],
) -> CountryNarrative | None:
    if not openrouter_is_configured():
        return None

    payload = {
        "country_name": country_name,
        "predicted_conflict_label": predicted_conflict_label,
        "region_name": region_name,
        "forecast_target": forecast_target,
        "horizon_days": horizon_days,
        "risk_level": risk_level,
        "forecast_probability": forecast_probability,
        "summary_fallback": summary_fallback,
        "social_summary_fallback": social_summary_fallback,
        "social_headline_fallback": social_headline_fallback,
        "social_body_fallback": social_body_fallback,
        "top_drivers": top_drivers,
        "chronology": chronology,
    }
    cache_path = _cache_path(payload)
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            return CountryNarrative(
                report_summary=_safe_text(cached.get("report_summary"), summary_fallback),
                social_summary_line=_safe_text(cached.get("social_summary_line"), social_summary_fallback),
                social_headline=_safe_text(cached.get("social_headline"), social_headline_fallback),
                social_body=_safe_text(cached.get("social_body"), social_body_fallback),
            )
        except (OSError, json.JSONDecodeError):
            pass

    api_key = os.getenv("OPENROUTER_API_KEY")
    model = resolve_openrouter_model()
    base_url = resolve_openrouter_base_url()
    if not api_key:
        return None

    prompt = {
        "country": country_name,
        "predicted_conflict_label": predicted_conflict_label,
        "region": region_name,
        "forecast_target": forecast_target,
        "horizon_days": horizon_days,
        "risk_level": risk_level,
        "forecast_probability": forecast_probability,
        "top_drivers": top_drivers,
        "chronology": chronology,
        "fallbacks": {
            "report_summary": summary_fallback,
            "social_summary_line": social_summary_fallback,
            "social_headline": social_headline_fallback,
            "social_body": social_body_fallback,
        },
    }
    body = {
        "model": model,
        "temperature": 0.2,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You write sober geopolitical early-warning copy for an intelligence dashboard. "
                    "Return strict JSON with keys report_summary, social_summary_line, social_headline, social_body. "
                    "Base every statement only on the provided inputs. Explain why the system is monitoring the named country "
                    "or predicted conflict label, citing the strongest drivers and chronology facts when useful. "
                    "If the evidence is weak or labels are unknown, say monitoring only or current watch instead of implying certainty. "
                    "Do not invent actors, events, dates, probabilities, battlefield claims, or outcomes. "
                    "Keep report_summary to 1-2 sentences, social_summary_line to 1 sentence, social_headline under 80 characters, "
                    "and social_body to at most 2 short sentences."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(prompt, ensure_ascii=False),
            },
        ],
        "response_format": {"type": "json_object"},
    }

    req = request.Request(
        base_url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=30) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (TimeoutError, OSError, error.HTTPError, json.JSONDecodeError):
        return None

    try:
        content = raw["choices"][0]["message"]["content"]
        parsed = json.loads(_strip_code_fences(content))
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None

    narrative = CountryNarrative(
        report_summary=_safe_text(parsed.get("report_summary"), summary_fallback),
        social_summary_line=_safe_text(parsed.get("social_summary_line"), social_summary_fallback),
        social_headline=_safe_text(parsed.get("social_headline"), social_headline_fallback),
        social_body=_safe_text(parsed.get("social_body"), social_body_fallback),
    )

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps(
                {
                    "report_summary": narrative.report_summary,
                    "social_summary_line": narrative.social_summary_line,
                    "social_headline": narrative.social_headline,
                    "social_body": narrative.social_body,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    except OSError:
        pass

    return narrative
