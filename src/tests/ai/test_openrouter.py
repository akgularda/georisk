from __future__ import annotations

import json
from typing import Any

import pytest

from src.ai import openrouter


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _narrative_kwargs() -> dict[str, Any]:
    return {
        "country_name": "Lebanon",
        "region_name": "Middle East",
        "predicted_conflict_label": "Lebanon / Israel",
        "forecast_target": "label_escalation_30d",
        "horizon_days": 30,
        "risk_level": "high",
        "forecast_probability": 0.84,
        "summary_fallback": "Fallback report summary.",
        "social_summary_fallback": "Fallback social summary.",
        "social_headline_fallback": "Fallback headline",
        "social_body_fallback": "Fallback social body.",
        "top_drivers": ["ACLED events (28d): 12"],
        "chronology": ["Week of 2026-03-23: pressure remained elevated."],
    }


def test_openrouter_defaults_require_only_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)

    assert openrouter.openrouter_is_configured() is True
    assert openrouter.resolve_openrouter_model() == "openrouter/free"
    assert openrouter.resolve_openrouter_base_url() == openrouter.DEFAULT_BASE_URL


@pytest.mark.parametrize("content", [None, "", "   "])
def test_openrouter_empty_content_returns_none(monkeypatch, tmp_path, content: object) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(openrouter, "CACHE_DIR", tmp_path)

    def fake_urlopen(req: object, timeout: int) -> _FakeResponse:
        return _FakeResponse({"choices": [{"message": {"content": content}}]})

    monkeypatch.setattr(openrouter.request, "urlopen", fake_urlopen)

    assert openrouter.maybe_generate_country_narrative(**_narrative_kwargs()) is None


def test_openrouter_blank_env_uses_defaults(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "")

    assert openrouter.openrouter_is_configured() is True
    assert openrouter.resolve_openrouter_model() == "openrouter/free"
    assert openrouter.resolve_openrouter_base_url() == openrouter.DEFAULT_BASE_URL
