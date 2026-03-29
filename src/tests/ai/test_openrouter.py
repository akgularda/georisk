from __future__ import annotations

from src.ai import openrouter


def test_openrouter_defaults_require_only_api_key(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    monkeypatch.delenv("OPENROUTER_BASE_URL", raising=False)

    assert openrouter.openrouter_is_configured() is True
    assert openrouter.resolve_openrouter_model() == "openrouter/free"
    assert openrouter.resolve_openrouter_base_url() == openrouter.DEFAULT_BASE_URL


def test_openrouter_blank_env_uses_defaults(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "")
    monkeypatch.setenv("OPENROUTER_BASE_URL", "")

    assert openrouter.openrouter_is_configured() is True
    assert openrouter.resolve_openrouter_model() == "openrouter/free"
    assert openrouter.resolve_openrouter_base_url() == openrouter.DEFAULT_BASE_URL
