"""Explainable, configuration-driven preliminary SNAP income screening."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "eligibility_rules.json"


@dataclass(frozen=True)
class ScreeningResult:
    status: str
    title_key: str
    explanation_keys: tuple[str, ...]
    monthly_income: float
    standard_limit: int
    expanded_limit: int
    source_url: str
    effective_from: str
    effective_to: str


def load_rules(path: Path = DATA_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def monthly_income(amount: float, frequency: str) -> float:
    """Normalize common pay frequencies using annualized monthly averages."""
    multipliers = {
        "weekly": 52 / 12,
        "biweekly": 26 / 12,
        "semimonthly": 2,
        "monthly": 1,
        "yearly": 1 / 12,
    }
    if frequency not in multipliers:
        raise ValueError(f"Unsupported income frequency: {frequency}")
    return round(max(0.0, float(amount)) * multipliers[frequency], 2)


def limit_for_household(table: dict[str, Any], size: int) -> int:
    if size < 1:
        raise ValueError("Household size must be at least 1")
    base_size = min(size, 8)
    limit = int(table["amounts"][str(base_size)])
    if size > 8:
        limit += (size - 8) * int(table["additional_member"])
    return limit


def screen_arizona(
    household_size: int,
    gross_monthly_income: float,
    has_elderly_or_disabled_member: bool,
    state: str = "AZ",
) -> ScreeningResult:
    """Return a cautious screening path, never an official eligibility decision."""
    rules = load_rules()
    if state != "AZ" or state not in rules["states"]:
        return ScreeningResult(
            status="unsupported",
            title_key="result_unsupported",
            explanation_keys=("explain_only_arizona",),
            monthly_income=gross_monthly_income,
            standard_limit=0,
            expanded_limit=0,
            source_url=rules["federal_source_url"],
            effective_from=rules["effective_from"],
            effective_to=rules["effective_to"],
        )

    az = rules["states"]["AZ"]
    standard = limit_for_household(az["gross_130"], household_size)
    expanded = limit_for_household(az["expanded_200"], household_size)
    common = dict(
        monthly_income=round(float(gross_monthly_income), 2),
        standard_limit=standard,
        expanded_limit=expanded,
        source_url=az["policy_source_url"],
        effective_from=rules["effective_from"],
        effective_to=rules["effective_to"],
    )

    if has_elderly_or_disabled_member:
        return ScreeningResult(
            status="needs_net_test",
            title_key="result_des_confirm",
            explanation_keys=("explain_net_only_plain", "explain_apply_unsure", "explain_official_decision_plain"),
            **common,
        )
    if gross_monthly_income <= standard:
        return ScreeningResult(
            status="passes_standard_gross",
            title_key="result_may_qualify",
            explanation_keys=("explain_under_130", "explain_net_test", "explain_official_decision"),
            **common,
        )
    if gross_monthly_income <= expanded:
        return ScreeningResult(
            status="possible_expanded",
            title_key="result_needs_review",
            explanation_keys=("explain_between_limits", "explain_net_test", "explain_official_decision"),
            **common,
        )
    return ScreeningResult(
        status="above_expanded_gross",
        title_key="result_unlikely_income",
        explanation_keys=("explain_over_200", "explain_official_decision"),
        **common,
    )
