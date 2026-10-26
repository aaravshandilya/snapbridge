from services.eligibility import limit_for_household, load_rules, monthly_income, screen_arizona


def test_income_frequency_normalization():
    assert monthly_income(600, "weekly") == 2600.0
    assert monthly_income(1200, "biweekly") == 2600.0
    assert monthly_income(36000, "yearly") == 3000.0


def test_current_arizona_thresholds_and_large_household():
    rules = load_rules()["states"]["AZ"]
    assert limit_for_household(rules["gross_130"], 1) == 1729
    assert limit_for_household(rules["gross_130"], 9) == 6653
    assert limit_for_household(rules["expanded_200"], 4) == 5500


def test_standard_gross_path_is_explainable():
    result = screen_arizona(3, 2500, False)
    assert result.status == "passes_standard_gross"
    assert result.standard_limit == 2960
    assert "explain_official_decision" in result.explanation_keys


def test_expanded_path_does_not_claim_eligibility():
    result = screen_arizona(3, 4000, False)
    assert result.status == "possible_expanded"
    assert result.title_key == "result_needs_review"


def test_elderly_or_disabled_routes_to_net_review():
    result = screen_arizona(1, 5000, True)
    assert result.status == "needs_net_test"
    assert result.title_key == "result_des_confirm"
    assert "explain_apply_unsure" in result.explanation_keys


def test_unsupported_state_refuses_estimate():
    result = screen_arizona(2, 1000, False, state="OTHER")
    assert result.status == "unsupported"
    assert result.standard_limit == 0
