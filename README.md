# SNAPBridge

**Bridging the gap between families and food assistance**

SNAPBridge is a privacy-first Streamlit application that helps Arizona households prepare for a SNAP (Nutrition Assistance) application. It offers an adaptive preliminary income screen, a guided preparation workflow, a tailored document checklist, a readiness dashboard, English/Spanish content, and an in-memory PDF worksheet.

> SNAPBridge is an independent educational and preparation tool. It is not affiliated with USDA or the Arizona Department of Economic Security (DES), does not submit an application, and does not determine eligibility. Only the responsible state agency can make an official eligibility and benefit decision.

## What works

- Four-step Arizona eligibility screening with conditional questions
- Current FY2027 Arizona income-rule configuration, effective October 1, 2026
- Explainable standard, expanded categorical, older-adult/disability, and unsupported-state outcomes
- Guided application preparation with Back/Next navigation and answer reuse
- Conditional document recommendations and collection progress
- Readiness score based on completed preparation milestones—not approval probability
- English and Spanish navigation, questions, explanations, checklist guidance, and FAQ
- PDF preparation worksheet and CSV checklist downloads
- Clear-session control and no server-side applicant storage
- Automated tests for rules, branching, recommendations, validation, readiness, and PDF output

## Architecture

```text
SNAPBridge/
├── app.py                         # Streamlit UI, navigation, session workflow
├── services/
│   ├── eligibility.py             # Rule loading and explainable income screening
│   ├── questionnaire.py           # Validation and readiness scoring
│   ├── documents.py               # Conditional document recommendation engine
│   ├── pdf_generator.py           # In-memory PDF worksheet
│   └── resources.py               # JSON and localization loading
├── data/
│   ├── eligibility_rules.json     # Versioned, dated, cited rule data
│   ├── official_portals.json      # Official Arizona and USDA links
│   └── questions.json             # Workflow metadata and excluded sensitive fields
├── translations/
│   ├── en.json
│   └── es.json
├── styles/custom.css
├── tests/
├── .streamlit/config.toml
└── requirements.txt
```

The UI never contains hard-coded eligibility thresholds. `eligibility.py` reads dated configuration from `data/eligibility_rules.json`. This keeps policy updates reviewable and testable. The screen intentionally does not approximate countable net income because Arizona's official calculation depends on source-specific income treatment, deductions, household rules, and categorical conditions.

## Verified sources

Rule data was last checked October 25, 2026.

- [Arizona DES eligibility and benefit determination policy](https://dbmefaapolicy.azdes.gov/FAA5/NA_Eligibility_and_Benefit_Determination.html)
- [Arizona 130% gross monthly standards](https://dbmefaapolicy.azdes.gov/FAA6/NA_Gross_Monthly_Income_Eligibility_Standard.html)
- [Arizona 200% FPL expanded categorical standard](https://dbmefaapolicy.azdes.gov/FAA6/NA_200__of_the_Federal_Poverty_Level.html)
- [USDA FY2027 SNAP standards](https://www.fna.usda.gov/snap/allotment/cola)
- [Arizona DES application guidance and possible verification items](https://des.az.gov/services/basic-needs/food-assistance/nutrition-assistance-na/how-apply-nutrition-assistance)
- [Official Health-e-Arizona Plus application](https://www.healthearizonaplus.gov/)

Rules change. Before a public launch or competition submission, recheck every configured effective date and source.

## Run locally

Python 3.11 or newer is recommended.

```bash
cd SNAPBridge
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local address printed by Streamlit, usually `http://localhost:8501`.

## Test

```bash
cd SNAPBridge
pytest -q
```

The tests use fictional values and never contain applicant information.

## Judge demo

1. Open the landing page and select **Get started**.
2. Enter a clearly identified fictional Arizona household in the screener.
3. Review the explainable result and its official sources.
4. Open **Documents**, mark items ready, and download the checklist.
5. Open **Prepare** and review the reused fictional answers.
6. Return to **Dashboard** and download the labeled PDF preparation worksheet.
7. Use the official portal link to demonstrate the handoff to Health-e-Arizona Plus.
8. Open **Privacy and session controls**, then clear the fictional information.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and place the contents of this `SNAPBridge` folder at its root (or note the subdirectory).
2. Push the repository to GitHub. Do not add applicant data or a `secrets.toml` file.
3. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/), select **Create app**, and choose the repository and branch.
4. Set the main file path to `app.py` (or `SNAPBridge/app.py` if this remains a subdirectory).
5. Deploy. No secrets, API keys, database, or paid service is required.
6. Test the English and Spanish paths, mobile layout, PDF download, checklist download, clear-session action, and every official link on the deployed URL.

Community Cloud creates isolated user sessions, but it is still a public service. The MVP therefore avoids accounts, uploads, permanent storage, and highly sensitive identifiers.

## Screenshot instructions

For a competition submission, capture at least these screens at a desktop width and one mobile width:

1. Home hero and privacy notice
2. Conditional screener question
3. Explainable screening result with dated source
4. Personalized document checklist
5. Readiness dashboard
6. Spanish FAQ or screener view

Use only clearly identified fictional test information. Crop out browser account details and save meaningful alt-text with each image.

## Privacy statement

SNAPBridge stores answers only in Streamlit's per-user session memory. It does not request Social Security numbers, banking credentials, identity-document uploads, or account passwords. It does not write responses to a database or shared file and does not send them to an external AI service. Answers disappear when the session expires or the user chooses **Clear My Information**. Downloaded files are saved only where the user chooses and are the user's responsibility.

Persistent accounts, saved applications, integrations, or uploads belong in a future phase only after authentication, encryption, access controls, retention/deletion policies, threat modeling, and security review.

## Accessibility notes

- Semantic Streamlit controls retain keyboard and screen-reader support.
- Visible labels and help text accompany inputs.
- Colors meet readable contrast goals and are not the only status signal.
- Responsive CSS avoids fixed-width layouts.
- Reduced-motion preferences are respected.
- English and Spanish strings live in centralized localization files.

A final submission should also be tested with keyboard-only navigation, VoiceOver or NVDA, browser zoom at 200%, and automated accessibility tooling.

## Known limitations

- Only Arizona has verified state rules.
- The screener does not calculate benefit amounts or official net income.
- It does not decide student, immigration, resource, or work-requirement eligibility.
- Expanded categorical eligibility requires conditions this MVP does not determine.
- Translations should receive review by a fluent Spanish-speaking benefits specialist before production use.
- Official websites and policies can change after the verification date.

## AI assistance disclosure

We used generative AI to help scaffold code, draft UX copy and tests, translate early interface text, and discover official sources. We then checked the policy data against the cited USDA and Arizona DES sources, ran the automated tests, reviewed the design and translations, and documented where AI helped. AI assistance supported the project; it did not replace the students' responsibility to understand and explain the app.

For the 2026 Congressional App Challenge, the team must fully disclose AI use, show significant student contributions and technical understanding, keep the team to four eligible students or fewer, and submit a public 1–3 minute demo video meeting the official content requirements.
