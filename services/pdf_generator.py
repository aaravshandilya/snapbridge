"""Local, in-memory PDF preparation worksheet generation."""
from __future__ import annotations

from io import BytesIO
from typing import Any, Callable

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_summary_pdf(data: dict[str, Any], documents: list[dict[str, Any]], t: Callable[..., str]) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=0.6 * inch, leftMargin=0.6 * inch)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleNavy", parent=styles["Title"], textColor=colors.HexColor("#17324D"), alignment=TA_CENTER)
    heading = ParagraphStyle("HeadingTeal", parent=styles["Heading2"], textColor=colors.HexColor("#0F766E"))
    story = [Paragraph("SNAPBridge", title), Paragraph(t("pdf_label"), styles["Heading3"]), Spacer(1, 12)]
    story.append(Paragraph(t("not_application_disclaimer"), styles["BodyText"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph(t("household_section"), heading))
    household_rows = [
        [t("state"), str(data.get("state", "—"))],
        [t("household_size"), str(data.get("household_size", "—"))],
        [t("children"), str(data.get("children", "—"))],
        [t("older_disabled"), t("yes") if data.get("elderly_disabled") else t("no")],
        [t("employment"), str(data.get("employment", "—"))],
    ]
    story.append(_table(household_rows))
    story.append(Spacer(1, 14))

    story.append(Paragraph(t("income_expenses_section"), heading))
    money_rows = [
        [t("reported_income"), f"${float(data.get('income_amount', 0)):,.2f} / {t(data.get('income_frequency', 'monthly'))}"],
        [t("monthly_income"), f"${float(data.get('monthly_income', 0)):,.2f}"],
        [t("rent"), f"${float(data.get('rent', 0)):,.2f}"],
        [t("utilities"), f"${float(data.get('utilities', 0)):,.2f}"],
        [t("childcare"), f"${float(data.get('childcare', 0)):,.2f}"],
        [t("medical"), f"${float(data.get('medical', 0)):,.2f}"],
        [t("child_support"), f"${float(data.get('child_support', 0)):,.2f}"],
    ]
    story.append(_table(money_rows))
    story.append(Spacer(1, 14))

    story.append(Paragraph(t("document_checklist"), heading))
    doc_rows = [[t("document"), t("priority"), t("collected")]]
    for item in documents:
        doc_rows.append([t(item["title_key"]), t(f"priority_{item['priority']}"), t("yes") if item.get("collected") else t("no")])
    story.append(_table(doc_rows, header=True))
    story.append(Spacer(1, 14))
    story.append(Paragraph(t("official_next_step"), heading))
    story.append(Paragraph("https://www.healthearizonaplus.gov/", styles["BodyText"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(t("privacy_short"), styles["Italic"]))
    doc.build(story)
    return buffer.getvalue()


def _table(rows: list[list[str]], header: bool = False) -> Table:
    table = Table(rows, colWidths=[2.25 * inch, 4.65 * inch], repeatRows=1 if header else 0)
    commands = [
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8F3FA")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17324D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])
    table.setStyle(TableStyle(commands))
    return table
