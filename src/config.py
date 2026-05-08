from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from .paths import TAXONOMY_CONFIG


@lru_cache(maxsize=1)
def load_taxonomy() -> dict[str, Any]:
    """Load taxonomy and scoring configuration from editable JSON."""
    return json.loads(TAXONOMY_CONFIG.read_text(encoding="utf-8"))


def topics() -> dict[str, dict[str, Any]]:
    return load_taxonomy()["topics"]


def product_areas() -> dict[str, list[str]]:
    return load_taxonomy()["product_areas"]


def sentiment_lexicons() -> tuple[dict[str, int], dict[str, int]]:
    sentiment = load_taxonomy()["sentiment"]
    return sentiment["positive"], sentiment["negative"]

