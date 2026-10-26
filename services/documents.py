"""Personalized, explainable document recommendation rules."""
from __future__ import annotations

from typing import Any


def _item(item_id: str, title_key: str, priority: str, reason_key: str, examples_key: str) -> dict[str, Any]:
    return {
        "id": item_id,
        "title_key": title_key,
        "priority": priority,
        "reason_key": reason_key,
        "examples_key": examples_key,
        "collected": False,
    }


def recommend_documents(data: dict[str, Any]) -> list[dict[str, Any]]:
    items = [
        _item("identity", "doc_identity", "required", "reason_identity", "example_identity"),
        _item("residency", "doc_residency", "required", "reason_residency", "example_residency"),
    ]
    if float(data.get("income_amount", 0)) > 0:
        items.append(_item("income", "doc_income", "required", "reason_income", "example_income"))
    if float(data.get("rent", 0)) > 0:
        items.append(_item("housing", "doc_housing", "potential", "reason_housing", "example_housing"))
    if float(data.get("utilities", 0)) > 0:
        items.append(_item("utilities", "doc_utilities", "potential", "reason_utilities", "example_utilities"))
    if float(data.get("childcare", 0)) > 0:
        items.append(_item("childcare", "doc_childcare", "potential", "reason_childcare", "example_childcare"))
    if data.get("elderly_disabled") and float(data.get("medical", 0)) > 35:
        items.append(_item("medical", "doc_medical", "potential", "reason_medical", "example_medical"))
    if float(data.get("child_support", 0)) > 0:
        items.append(_item("child_support", "doc_child_support", "potential", "reason_child_support", "example_child_support"))
    items.append(_item("notes", "doc_notes", "optional", "reason_notes", "example_notes"))
    return items


def merge_collection_state(new_items: list[dict[str, Any]], old_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    old_state = {item["id"]: bool(item.get("collected")) for item in old_items}
    for item in new_items:
        item["collected"] = old_state.get(item["id"], False)
    return new_items
