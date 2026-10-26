from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import streamlit as st

from services.documents import merge_collection_state, recommend_documents
from services.eligibility import monthly_income, screen_arizona
from services.pdf_generator import build_summary_pdf
from services.questionnaire import application_missing, readiness_score, validate_household, validate_income
from services.resources import official_resources, translator


ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="SNAPBridge", page_icon="🌉", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"<style>{(ROOT / 'styles' / 'custom.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


DEFAULTS = {
    "language": "en",
    "page": "home",
    "screen_step": 0,
    "assistant_step": 0,
    "state": "AZ",
    "household_size": 1,
    "children": 0,
    "elderly_disabled": False,
    "employment": "",
    "has_income": True,
    "income_amount": 0.0,
    "income_frequency": "monthly",
    "monthly_income": 0.0,
    "rent": 0.0,
    "utilities": 0.0,
    "childcare": 0.0,
    "medical": 0.0,
    "child_support": 0.0,
    "household_complete": False,
    "income_complete": False,
    "screening_complete": False,
    "review_complete": False,
    "official_portal_opened": False,
    "documents_data": [],
    "demo": False,
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value.copy() if isinstance(value, list) else value)


def go(page: str) -> None:
    st.session_state.pending_page = page
    st.rerun()


def load_demo() -> None:
    st.session_state.update({
        "demo": True, "state": "AZ", "household_size": 3, "children": 1,
        "elderly_disabled": True, "employment": "One or more people work",
        "has_income": True, "income_amount": 560.0, "income_frequency": "weekly",
        "monthly_income": monthly_income(560, "weekly"), "rent": 1250.0,
        "utilities": 210.0, "childcare": 325.0, "medical": 85.0,
        "child_support": 0.0, "household_complete": True, "income_complete": True,
        "screening_complete": True, "review_complete": True, "screen_step": 3,
        "assistant_step": 2,
    })
    st.session_state.documents_data = recommend_documents(dict(st.session_state))


def clear_data() -> None:
    language = st.session_state.get("language", "en")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state.language = language
    st.session_state.cleared_notice = True
    init_state()


def sync_documents() -> None:
    fresh = recommend_documents(dict(st.session_state))
    st.session_state.documents_data = merge_collection_state(fresh, st.session_state.documents_data)


def header_notice(t) -> None:
    st.markdown(f'<div class="notice"><strong>{t("independent_notice")}</strong><br>{t("government_disclaimer")}</div>', unsafe_allow_html=True)


def render_home(t) -> None:
    st.markdown(
        f'<section class="hero"><div class="eyebrow">{t("tagline")}</div>'
        f'<h1>{t("hero_title")}</h1><p>{t("hero_body")}</p></section>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1])
    if c1.button(t("get_started"), type="primary", use_container_width=True):
        go("screener")
    if c2.button(t("explore_demo"), use_container_width=True):
        load_demo()
        go("dashboard")

    st.write("")
    cols = st.columns(3)
    cards = [
        ("🛡️", t("privacy_first"), t("privacy_body")),
        ("↪️", t("adaptive"), t("adaptive_body")),
        ("🔎", t("explainable"), t("explainable_body")),
    ]
    for col, (icon, title, body) in zip(cols, cards):
        col.markdown(f'<div class="card"><div class="icon">{icon}</div><h3>{title}</h3><p>{body}</p></div>', unsafe_allow_html=True)

    st.write("")
    st.subheader(t("workflow_title"))
    for number in range(1, 6):
        st.markdown(f'<div class="step-card"><span class="step-number">{number}</span><span>{t(f"workflow_{number}")}</span></div>', unsafe_allow_html=True)
    st.info(t("supported_state"))


def render_screener(t) -> None:
    st.title(t("screener"))
    header_notice(t)
    step = st.session_state.screen_step
    st.caption(t("section_of", current=min(step + 1, 4), total=4))
    st.progress(min((step + 1) / 4, 1.0))

    if step == 0:
        st.subheader(t("household_section"))
        state_choice = st.selectbox(t("state"), [t("arizona"), t("other_state")], help=t("state_help"))
        state = "AZ" if state_choice == t("arizona") else "OTHER"
        household_size = st.number_input(t("household_size"), 1, 20, int(st.session_state.household_size), help=t("household_help"))
        children = st.number_input(t("children"), 0, int(household_size), min(int(st.session_state.children), int(household_size)))
        elderly_disabled = st.checkbox(t("older_disabled"), value=st.session_state.elderly_disabled, help=t("older_disabled_help"))
        employment_options = t("employment_options")
        current_index = employment_options.index(st.session_state.employment) if st.session_state.employment in employment_options else 0
        employment = st.selectbox(t("employment"), employment_options, index=current_index)
        if st.button(t("next"), type="primary"):
            payload = {"state": state, "household_size": household_size, "children": children}
            if validate_household(payload):
                st.error(t("validation_error"))
            else:
                st.session_state.update(payload | {"elderly_disabled": elderly_disabled, "employment": employment, "household_complete": True, "screen_step": 1})
                st.rerun()

    elif step == 1:
        st.subheader(t("income_expenses_section"))
        has_income = st.radio(t("income_prompt"), [True, False], format_func=lambda x: t("yes") if x else t("no"), horizontal=True, index=0 if st.session_state.has_income else 1)
        amount = st.number_input(t("income_amount"), min_value=0.0, value=float(st.session_state.income_amount), step=25.0, help=t("gross_help"), disabled=not has_income)
        frequency_codes = ["weekly", "biweekly", "semimonthly", "monthly", "yearly"]
        frequency = st.selectbox(t("income_frequency"), frequency_codes, format_func=t, index=frequency_codes.index(st.session_state.income_frequency), disabled=not has_income)
        c1, c2 = st.columns(2)
        if c1.button(t("back"), use_container_width=True):
            st.session_state.screen_step = 0
            st.rerun()
        if c2.button(t("next"), type="primary", use_container_width=True):
            amount = amount if has_income else 0.0
            payload = {"income_amount": amount, "income_frequency": frequency}
            if validate_income(payload):
                st.error(t("validation_error"))
            else:
                st.session_state.update(payload | {"has_income": has_income, "monthly_income": monthly_income(amount, frequency), "screen_step": 2})
                st.rerun()

    elif step == 2:
        st.subheader(t("income_expenses_section"))
        st.info(t("expense_intro"))
        rent = st.number_input(t("rent"), min_value=0.0, value=float(st.session_state.rent), step=25.0)
        utilities = st.number_input(t("utilities"), min_value=0.0, value=float(st.session_state.utilities), step=10.0)
        childcare = st.number_input(t("childcare"), min_value=0.0, value=float(st.session_state.childcare), step=25.0)
        medical = 0.0
        if st.session_state.elderly_disabled:
            medical = st.number_input(t("medical"), min_value=0.0, value=float(st.session_state.medical), step=10.0)
        child_support = st.number_input(t("child_support"), min_value=0.0, value=float(st.session_state.child_support), step=25.0)
        c1, c2 = st.columns(2)
        if c1.button(t("back"), use_container_width=True):
            st.session_state.screen_step = 1
            st.rerun()
        if c2.button(t("review"), type="primary", use_container_width=True):
            payload = {"rent": rent, "utilities": utilities, "childcare": childcare, "medical": medical, "child_support": child_support}
            if validate_income(payload | {"income_amount": st.session_state.income_amount, "income_frequency": st.session_state.income_frequency}):
                st.error(t("validation_error"))
            else:
                st.session_state.update(payload | {"income_complete": True, "screening_complete": True, "screen_step": 3})
                sync_documents()
                st.rerun()
    else:
        render_screening_result(t)


def render_screening_result(t) -> None:
    result = screen_arizona(
        int(st.session_state.household_size), float(st.session_state.monthly_income),
        bool(st.session_state.elderly_disabled), str(st.session_state.state),
    )
    style = {"passes_standard_gross": "result-good", "above_expanded_gross": "result-caution"}.get(result.status, "result-review")
    st.subheader(t("result_heading"))
    st.markdown(f'<div class="{style}"><h3>{t(result.title_key)}</h3></div>', unsafe_allow_html=True)
    if result.status != "unsupported":
        st.markdown(
            f'<div class="metric-strip"><div class="metric-box"><small>{t("estimated_monthly")}</small><strong>${result.monthly_income:,.0f}</strong></div>'
            f'<div class="metric-box"><small>{t("standard_limit")}</small><strong>${result.standard_limit:,.0f}</strong></div>'
            f'<div class="metric-box"><small>{t("expanded_limit")}</small><strong>${result.expanded_limit:,.0f}</strong></div></div>',
            unsafe_allow_html=True,
        )
    for key in result.explanation_keys:
        st.write(f"• {t(key)}")
    st.caption(t("rules_effective", start=result.effective_from, end=result.effective_to))
    st.link_button(t("view_source"), result.source_url)
    c1, c2 = st.columns(2)
    if c1.button(t("back"), use_container_width=True):
        st.session_state.screen_step = 2
        st.rerun()
    if c2.button(t("continue_assistant"), type="primary", use_container_width=True):
        go("assistant")


def render_assistant(t) -> None:
    st.title(t("assistant_title"))
    st.write(t("assistant_intro"))
    header_notice(t)
    if not st.session_state.household_complete:
        st.warning(t("missing_info"))
        if st.button(t("get_started"), type="primary"):
            go("screener")
        return
    step = st.session_state.assistant_step
    st.caption(t("section_of", current=step + 1, total=3))
    st.progress((step + 1) / 3)
    if step == 0:
        st.subheader(t("household_section"))
        st.info(f'**{t("why_matters")}:** {t("why_household")}')
        st.write(f'**{t("state")}:** {st.session_state.state}')
        st.write(f'**{t("household_size")}:** {st.session_state.household_size}')
        st.write(f'**{t("children")}:** {st.session_state.children}')
        if st.button(t("next"), type="primary"):
            st.session_state.assistant_step = 1
            st.rerun()
    elif step == 1:
        st.subheader(t("income_expenses_section"))
        st.info(f'**{t("why_matters")}:** {t("why_income")}')
        st.write(f'**{t("monthly_income")}:** ${st.session_state.monthly_income:,.2f}')
        for key in ("rent", "utilities", "childcare", "medical", "child_support"):
            if float(st.session_state.get(key, 0)) > 0:
                st.write(f'**{t(key)}:** ${st.session_state[key]:,.2f}')
        c1, c2 = st.columns(2)
        if c1.button(t("back"), use_container_width=True):
            st.session_state.assistant_step = 0
            st.rerun()
        if c2.button(t("next"), type="primary", use_container_width=True):
            st.session_state.assistant_step = 2
            st.rerun()
    else:
        st.subheader(t("review_title"))
        render_review_table(t)
        c1, c2, c3 = st.columns(3)
        if c1.button(t("edit_household"), use_container_width=True):
            st.session_state.screen_step = 0
            go("screener")
        if c2.button(t("edit_income"), use_container_width=True):
            st.session_state.screen_step = 1
            go("screener")
        if c3.button(t("complete_preparation"), type="primary", use_container_width=True):
            st.session_state.review_complete = True
            sync_documents()
            go("documents")


def render_review_table(t) -> None:
    rows = {
        t("state"): st.session_state.state,
        t("household_size"): st.session_state.household_size,
        t("children"): st.session_state.children,
        t("older_disabled"): t("yes") if st.session_state.elderly_disabled else t("no"),
        t("monthly_income"): f'${st.session_state.monthly_income:,.2f}',
        t("rent"): f'${st.session_state.rent:,.2f}',
        t("utilities"): f'${st.session_state.utilities:,.2f}',
        t("childcare"): f'${st.session_state.childcare:,.2f}',
        t("medical"): f'${st.session_state.medical:,.2f}',
    }
    for label, value in rows.items():
        st.markdown(f"**{label}:** {value}")


def render_documents(t) -> None:
    st.title(t("document_checklist"))
    st.write(t("documents_intro"))
    if not st.session_state.documents_data:
        sync_documents()
    docs = st.session_state.documents_data
    for item in docs:
        with st.container(border=True):
            left, right = st.columns([5, 1])
            priority_label = t(f"priority_{item['priority']}")
            left.markdown(f'**{t(item["title_key"])}**  \n`{priority_label}`')
            left.markdown(f'<div class="doc-reason">{t(item["reason_key"])}<br><em>{t(item["examples_key"])}</em></div>', unsafe_allow_html=True)
            item["collected"] = right.checkbox(t("collected"), value=bool(item["collected"]), key=f'doc_{item["id"]}', label_visibility="visible")
    done = sum(bool(item["collected"]) for item in docs)
    st.progress(done / len(docs) if docs else 0)
    st.caption(t("progress_collected", done=done, total=len(docs)))
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([t("document"), t("priority"), t("collected")])
    for item in docs:
        writer.writerow([t(item["title_key"]), t(f"priority_{item['priority']}"), t("yes") if item["collected"] else t("no")])
    st.download_button(t("download_checklist"), output.getvalue().encode("utf-8-sig"), "SNAPBridge_document_checklist.csv", "text/csv", use_container_width=True)


def render_dashboard(t) -> None:
    st.title(t("dashboard_title"))
    sync_documents()
    docs = st.session_state.documents_data
    score_data = dict(st.session_state)
    score_data["review_complete"] = st.session_state.review_complete
    score = readiness_score(score_data, docs)
    st.metric(t("readiness"), f"{score}%")
    st.progress(score / 100)
    st.caption(t("readiness_disclaimer"))
    milestones = [
        ("milestone_household", st.session_state.household_complete),
        ("milestone_income", st.session_state.income_complete),
        ("milestone_screen", st.session_state.screening_complete),
        ("milestone_documents", bool(docs) and all(i["collected"] for i in docs if i["priority"] == "required")),
        ("milestone_review", st.session_state.review_complete),
        ("milestone_portal", st.session_state.official_portal_opened),
    ]
    st.subheader(t("milestones"))
    for key, complete in milestones:
        symbol = "✓" if complete else "○"
        css = "status-complete" if complete else "status-open"
        st.markdown(f'<div class="step-card"><span class="{css}">{symbol}</span><span>{t(key)}</span></div>', unsafe_allow_html=True)

    missing = application_missing(dict(st.session_state))
    st.subheader(t("next_steps"))
    if missing:
        st.warning(f'{t("missing_info")}: {", ".join(t(item) for item in missing)}')
    elif score == 100:
        st.success(t("all_ready"))
    else:
        for key, complete in milestones:
            if not complete:
                st.write(f"• {t(key)}")

    if st.session_state.household_complete:
        pdf = build_summary_pdf(dict(st.session_state), docs, t)
        st.download_button(t("download_pdf"), pdf, "SNAPBridge_preparation_worksheet.pdf", "application/pdf", type="primary", use_container_width=True)
    st.warning(t("portal_notice"))
    portal = official_resources()["AZ"]["apply_url"]
    st.link_button(t("open_official_portal"), portal, use_container_width=True)
    if st.button(f'✓ {t("milestone_portal")}', use_container_width=True):
        st.session_state.official_portal_opened = True
        st.rerun()


def render_resources(t) -> None:
    st.title(t("faq_title"))
    query = st.text_input(t("faq_search")).strip().lower()
    faqs = [("faq_what", "faq_what_a"), ("faq_who", "faq_who_a"), ("faq_income", "faq_income_a"), ("faq_docs", "faq_docs_a"), ("faq_apply", "faq_apply_a"), ("faq_after", "faq_after_a"), ("faq_missing_doc", "faq_missing_doc_a")]
    visible = [(q, a) for q, a in faqs if not query or query in t(q).lower() or query in t(a).lower()]
    for question, answer in visible:
        with st.expander(t(question)):
            st.write(t(answer))
    st.subheader(t("official_resources"))
    resources = official_resources()
    st.link_button(t("des_overview"), resources["AZ"]["des_overview_url"], use_container_width=True)
    st.link_button(t("how_to_apply"), resources["AZ"]["how_to_apply_url"], use_container_width=True)
    st.link_button(t("usda_rules"), resources["USDA"]["cola_url"], use_container_width=True)
    st.info(t("contact_des"))


def render_about(t) -> None:
    st.title(t("about_title"))
    sections = [("mission", "mission_body"), ("technology", "technology_body"), ("privacy", "privacy_body_long"), ("limitations", "limitations_body"), ("challenge", "challenge_body"), ("ai_use", "ai_use_body")]
    for title, body in sections:
        st.subheader(t(title))
        st.write(t(body))


init_state()
pending_page = st.session_state.pop("pending_page", None)
if pending_page:
    st.session_state.page = pending_page
    st.session_state.nav_radio = pending_page
elif "nav_radio" not in st.session_state:
    st.session_state.nav_radio = st.session_state.page
language_label = st.sidebar.selectbox("Language / Idioma", ["English", "Español"], index=0 if st.session_state.language == "en" else 1)
st.session_state.language = "es" if language_label == "Español" else "en"
t = translator(st.session_state.language)
st.sidebar.markdown(f'<div class="brand-mark"><span class="brand-icon">S</span>{t("app_name")}</div><div class="source-note">{t("tagline")}</div>', unsafe_allow_html=True)
st.sidebar.write("")
pages = ["home", "screener", "assistant", "documents", "dashboard", "resources", "about"]
labels = {key: t(key) for key in pages}
selected = st.sidebar.radio("Navigation", pages, format_func=lambda key: labels[key], key="nav_radio", label_visibility="collapsed")
st.session_state.page = selected
st.sidebar.divider()
if st.sidebar.button(f'✨ {t("demo_mode")}', help=t("demo_help"), use_container_width=True):
    load_demo()
    go("dashboard")
if st.sidebar.button(f'🗑️ {t("clear_data")}', use_container_width=True):
    clear_data()
    st.rerun()
if st.session_state.get("cleared_notice"):
    st.sidebar.success(t("data_cleared"))
    st.session_state.cleared_notice = False
if st.session_state.demo:
    st.sidebar.info(f'✨ {t("demo_mode")}')

renderers = {
    "home": render_home, "screener": render_screener, "assistant": render_assistant,
    "documents": render_documents, "dashboard": render_dashboard,
    "resources": render_resources, "about": render_about,
}
renderers[st.session_state.page](t)
st.markdown(f'<div class="footer">{t("footer")}</div>', unsafe_allow_html=True)
