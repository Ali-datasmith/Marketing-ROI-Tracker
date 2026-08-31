from datetime import datetime
from typing import Any

from fpdf import FPDF

from ai.insights_engine import MarketingInsightsReport


def sanitize_utf8(text: str) -> str:
    """
    Sanitize text strings for latin-1 safe FPDF2 rendering.
    Replaces non-latin-1 currency symbols and bullet points with ASCII equivalents.
    """
    if not isinstance(text, str):
        return str(text)
    replacements = {
        "•": "-",
        "—": "-",
        "–": "-",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "€": "EUR ",
        "£": "GBP ",
        "¥": "JPY ",
        "₹": "INR ",
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return text.encode("latin-1", "replace").decode("latin-1")


class ExecutiveBriefPDF(FPDF):
    """Custom FPDF2 Generator for Executive Marketing ROI & Attribution Brief."""

    def header(self) -> None:
        self.set_fill_color(11, 15, 25)
        self.rect(0, 0, 210, 297, "F")

        self.set_font("Helvetica", "B", 18)
        self.set_text_color(0, 229, 255)
        self.cell(
            0, 10, sanitize_utf8("B2B MULTI-TOUCH ATTRIBUTION BRIEF"), new_x="LMARGIN", new_y="NEXT", align="L"
        )

        self.set_font("Helvetica", "I", 10)
        self.set_text_color(160, 174, 192)
        time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(
            0,
            6,
            sanitize_utf8(f"Generated on {time_str} | Executive C-Suite Report"),
            new_x="LMARGIN",
            new_y="NEXT",
            align="L",
        )
        self.ln(5)

        self.set_draw_color(0, 229, 255)
        self.set_line_width(0.8)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self) -> None:
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(113, 128, 150)
        self.cell(
            0,
            10,
            sanitize_utf8(f"Page {self.page_no()} | Marketing ROI Engine (Enterprise Edition)"),
            align="C",
        )


def generate_executive_pdf(
    summary_metrics: dict[str, Any],
    report: MarketingInsightsReport,
    output_filename: str = "Executive_Marketing_ROI_Brief.pdf",
) -> bytes:
    """Generate dark-themed executive C-suite PDF summary report with exact metric parity."""
    pdf = ExecutiveBriefPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 1. Executive KPI Overview
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, sanitize_utf8("1. Executive KPI Overview"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_fill_color(21, 29, 46)
    pdf.set_text_color(226, 232, 240)

    spend = f"${summary_metrics.get('total_spend', 0.0):,.2f}"
    revenue = f"${summary_metrics.get('total_revenue', 0.0):,.2f}"
    roas = f"{summary_metrics.get('overall_roas', 0.0):.2f}x"
    cpa = f"${summary_metrics.get('overall_cpa', 0.0):,.2f}"
    cac = f"${summary_metrics.get('overall_cac', summary_metrics.get('overall_cpa', 0.0)):,.2f}"
    conversions = f"{summary_metrics.get('total_conversions', 0.0):,.1f}"

    kpi_line1 = sanitize_utf8(f"Total Spend: {spend}  |  Total Revenue: {revenue}  |  Conversions: {conversions}")
    kpi_line2 = sanitize_utf8(f"Blended ROAS: {roas}  |  Blended CPA: {cpa}  |  Blended CAC: {cac}")

    pdf.cell(190, 8, kpi_line1, border=1, fill=True, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.cell(190, 8, kpi_line2, border=1, fill=True, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)

    # 2. AI Performance Synthesis
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, sanitize_utf8("2. AI Performance Synthesis"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(203, 213, 225)
    pdf.multi_cell(190, 6, sanitize_utf8(report.executive_summary))
    pdf.ln(4)

    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(0, 229, 255)
    pdf.multi_cell(190, 6, sanitize_utf8(f"Blended ROAS Assessment: {report.blended_roas_assessment}"))
    pdf.ln(6)

    # 3. Recommended Budget Reallocations
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, sanitize_utf8("3. Recommended Budget Reallocations"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for rec in report.budget_recommendations:
        pdf.set_font("Helvetica", "B", 10)
        action_color = (
            (16, 185, 129)
            if rec.action == "INCREASE"
            else ((239, 68, 68) if rec.action == "DECREASE" else (245, 158, 11))
        )
        pdf.set_text_color(*action_color)
        pdf.cell(
            0,
            6,
            sanitize_utf8(f"- {rec.channel}: [{rec.action} by {rec.percentage_change:.1f}%]"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(160, 174, 192)
        pdf.multi_cell(185, 5, sanitize_utf8(f"  Rationale: {rec.rationale}"))
        pdf.ln(2)

    pdf.ln(4)

    # 4. Identified Channel Risks
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 8, sanitize_utf8("4. Identified Channel Risks"), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for risk in report.risk_factors:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(248, 113, 113)
        pdf.cell(
            0,
            6,
            sanitize_utf8(f"- [{risk.severity}] {risk.channel} - {risk.category}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(160, 174, 192)
        pdf.multi_cell(185, 5, sanitize_utf8(f"  {risk.description}"))
        pdf.ln(2)

    return bytes(pdf.output())
