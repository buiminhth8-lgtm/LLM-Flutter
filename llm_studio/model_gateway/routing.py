"""Minimal provider / profile routing for Model Gateway."""

from __future__ import annotations

from .schemas import ModelProfile

DEFAULT_PROVIDER = "fake"


def resolve_provider_name(
    provider: str | None,
    profile: ModelProfile | None = None,
) -> str:
    """Resolve the provider name for a request.

    Rules:
    1. If ``provider`` is set, use it.
    2. Otherwise use ``profile.provider`` when a profile exists.
    3. Otherwise fall back to the default ``fake`` provider.

    No database or config access.
    """
    if provider and provider.strip():
        return provider.strip()
    if profile is not None and profile.provider:
        return profile.provider
    return DEFAULT_PROVIDER
