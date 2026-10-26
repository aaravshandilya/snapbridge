from services.questionnaire import readiness_score, validate_household, validate_income


def test_validation_rejects_impossible_household():
    assert "children" in validate_household({"state": "AZ", "household_size": 2, "children": 3})


def test_validation_rejects_negative_money():
    errors = validate_income({"income_amount": -1, "income_frequency": "monthly", "rent": -10})
    assert "income_amount" in errors and "rent" in errors


def test_readiness_is_preparation_not_eligibility():
    data = {
        "state": "AZ", "household_size": 2, "income_amount": 100,
        "income_frequency": "monthly", "employment": "work",
        "household_complete": True, "income_complete": True, "screening_complete": True,
        "review_complete": True,
    }
    docs = [{"priority": "required", "collected": True}]
    assert readiness_score(data, docs) == 100


def test_opening_portal_does_not_change_readiness():
    data = {
        "state": "AZ", "household_size": 2, "income_amount": 100,
        "income_frequency": "monthly", "employment": "work",
        "household_complete": True, "income_complete": True, "screening_complete": True,
        "review_complete": True, "official_portal_opened": False,
    }
    docs = [{"priority": "required", "collected": True}]
    before = readiness_score(data, docs)
    data["official_portal_opened"] = True
    assert readiness_score(data, docs) == before == 100


def test_pdf_generation_returns_pdf_bytes():
    from services.pdf_generator import build_summary_pdf

    pdf = build_summary_pdf({"state": "AZ"}, [], lambda key, **kwargs: key)
    assert pdf.startswith(b"%PDF")
