"""Shared questionnaire helpers and validation."""
from __future__ import annotations

from typing import Any


FREQUENCIES = ("weekly", "biweekly", "semimonthly", "monthly", "yearly")


def validate_household(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not data.get("state"):
        errors.append("state")
    if int(data.get("household_size", 0)) < 1:
        errors.append("household_size")
    if int(data.get("children", 0)) > int(data.get("household_size", 0)):
        errors.append("children")
    return errors


def validate_income(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if float(data.get("income_amount", -1)) < 0:
        errors.append("income_amount")
    if data.get("income_frequency") not in FREQUENCIES:
        errors.append("income_frequency")
    for field in ("rent", "utilities", "childcare", "medical", "child_support"):
        if float(data.get(field, 0)) < 0:
            errors.append(field)
    return errors


def application_missing(data: dict[str, Any]) -> list[str]:
    required = ("state", "household_size", "income_amount", "income_frequency", "employment")
    return [field for field in required if data.get(field) in (None, "")]


def readiness_score(data: dict[str, Any], document_items: list[dict[str, Any]]) -> int:
    """Measure preparation completion only; this is not an approval probability."""
    milestones = [
        bool(data.get("household_complete")),
        bool(data.get("income_complete")),
        bool(data.get("screening_complete")),
        bool(document_items) and all(item.get("collected", False) for item in document_items if item["priority"] == "required"),
        bool(data.get("review_complete")) and not application_missing(data),
    ]
    return round(sum(milestones) / len(milestones) * 100)
