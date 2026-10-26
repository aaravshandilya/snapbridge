from services.documents import merge_collection_state, recommend_documents


def test_document_rules_are_conditional():
    docs = recommend_documents({
        "income_amount": 500, "rent": 1000, "utilities": 0, "childcare": 250,
        "elderly_disabled": True, "medical": 40, "child_support": 0,
    })
    ids = {item["id"] for item in docs}
    assert {"identity", "residency", "income", "housing", "childcare", "medical"} <= ids
    assert "utilities" not in ids
    assert "child_support" not in ids


def test_medical_documents_require_both_conditions():
    assert "medical" not in {d["id"] for d in recommend_documents({"elderly_disabled": False, "medical": 100})}
    assert "medical" not in {d["id"] for d in recommend_documents({"elderly_disabled": True, "medical": 35})}


def test_collection_state_survives_recommendation_refresh():
    old = recommend_documents({})
    old[0]["collected"] = True
    merged = merge_collection_state(recommend_documents({"rent": 1}), old)
    assert merged[0]["collected"] is True
