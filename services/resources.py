"""Loading centralized localization and official resources."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative_path: str) -> dict[str, Any]:
    with (ROOT / relative_path).open(encoding="utf-8") as handle:
        return json.load(handle)


def translator(language: str):
    values = load_json(f"translations/{language}.json")
    fallback = load_json("translations/en.json")

    def t(key: str, **kwargs: Any) -> str:
        value = values.get(key, fallback.get(key, key))
        return value.format(**kwargs) if kwargs else value

    return t


def official_resources() -> dict[str, Any]:
    return load_json("data/official_portals.json")
